"""Helpers shared by the migrations that clean the duplicated contacts (T3642)."""

import logging
import re
import unicodedata

from markupsafe import Markup, escape
from openupgradelib import openupgrade
from psycopg2.errors import UniqueViolation

from odoo import fields
from odoo.tools import SQL, mute_logger
from odoo.tools.mail import email_normalize

_logger = logging.getLogger(__name__)

# Tables that reference a partner with (model, res_id) instead of a foreign key
REFERENCE_TABLES = [
    ("mail_message", "model", "res_id"),
    ("mail_followers", "res_model", "res_id"),
    ("mail_activity", "res_model", "res_id"),
    ("ir_attachment", "res_model", "res_id"),
]
# User in charge of verifying the duplicated partners, as in partner_auto_match
REVIEW_USER_PARAM = "partner_auto_match.match_validation_responsible"
# Key set in the databases migrated from v14, which partner_auto_match ignores
LEGACY_REVIEW_USER_PARAM = "cms_form_compassion.match_validation_responsible"
# Name given by the "duplicate" action of Odoo to a copy
COPY_NAME = re.compile(r"\((copie|copy|kopie)\)", re.IGNORECASE)


def fix_review_user_param(env):
    """Rename the legacy setting to the key read by partner_auto_match, so that
    the user in charge also gets the activities of the new partners."""
    params = env["ir.config_parameter"].sudo()
    legacy = params.search([("key", "=", LEGACY_REVIEW_USER_PARAM)])
    if not legacy:
        return
    if not params.get_param(REVIEW_USER_PARAM):
        params.set_param(REVIEW_USER_PARAM, legacy.value)
        legacy.unlink()
        _logger.info(
            "T3642: %s renamed to %s", LEGACY_REVIEW_USER_PARAM, REVIEW_USER_PARAM
        )


# ----------------------------------------------------------------------------
# Which contacts are aliases
# ----------------------------------------------------------------------------
def _ascii(name):
    name = unicodedata.normalize("NFKD", name or "")
    return "".join(c for c in name if not unicodedata.combining(c)).lower()


def _normalize_name(name):
    return re.sub(r"[^a-z0-9]", "", _ascii(name))


def _name_tokens(name):
    return {t for t in re.findall(r"[a-z0-9]+", _ascii(name)) if len(t) > 2}


def is_v14_alias(name, parent_name, parent_is_company):
    """Tell whether a child of type "other" is a contact attached in v14.

    Their name was kept equal to the one of the main contact (it can be blank,
    or suffixed by "(copy)" when it was duplicated, or the same words in another
    order). Under a person, a name sharing a word with the main contact is kept
    as well (spelling, maiden or couple names). Anything else, like a contact
    person under a company, is a real child that has to be left untouched."""
    if not (name or "").strip() or COPY_NAME.search(name):
        return True
    if _normalize_name(name) == _normalize_name(parent_name):
        return True
    tokens, parent_tokens = _name_tokens(name), _name_tokens(parent_name)
    if tokens and tokens == parent_tokens:
        return True  # same words in another order
    if parent_is_company:
        return False
    return bool(tokens & parent_tokens)


# ----------------------------------------------------------------------------
# What an alias carries
# ----------------------------------------------------------------------------
def _existing_columns(cr, columns):
    cr.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'res_partner' AND column_name IN %s",
        (tuple(columns),),
    )
    return {row[0] for row in cr.fetchall()}


def _digits(number):
    return re.sub(r"\D", "", number or "")


def _address(row):
    return ((row.get("street") or "").strip().lower(), (row.get("zip") or "").strip())


def _phones(row):
    return {_digits(row.get("phone")), _digits(row.get("mobile"))} - {""}


def classify_aliases(cr, main):
    """Tell what the aliases carry compared to their main contact.

    The fields of modules that may not be loaded yet (CC flag, birthdate) are
    read with SQL.

    :param main: dict alias id -> main contact id
    :return: the set of aliases without data of their own (to archive) and the
             set of aliases with an e-mail address of their own
    """
    columns = ["email", "street", "zip", "phone", "mobile", "birthdate_date"]
    columns.append("email_copy")
    present = sorted(_existing_columns(cr, columns))
    cr.execute(
        SQL(
            "SELECT id, %s FROM res_partner WHERE id IN %s",
            SQL(", ").join(SQL.identifier(c) for c in present),
            tuple(set(main) | set(main.values())),
        )
    )
    rows = {row["id"]: row for row in cr.dictfetchall()}
    redundant = set()
    with_email = set()
    for alias_id, main_id in main.items():
        alias, contact = rows[alias_id], rows[main_id]
        alias_email = email_normalize(alias.get("email")) or ""
        contact_email = email_normalize(contact.get("email")) or ""
        own_email = bool(alias_email) and alias_email != contact_email
        own_address = any(_address(alias)) and _address(alias) != _address(contact)
        own_phone = bool(_phones(alias) - _phones(contact))
        birthdate = alias.get("birthdate_date")
        own_birthdate = bool(birthdate) and birthdate != contact.get("birthdate_date")
        if own_email:
            with_email.add(alias_id)
        if not (
            own_email
            or own_address
            or own_phone
            or own_birthdate
            or alias.get("email_copy")
        ):
            redundant.add(alias_id)
    return redundant, with_email


def apply_aliases(env, main, redundant, with_email):
    """Attach the contacts to their main contact, with SQL, to avoid the
    overrides of res.partner (tracking, synchronization with other systems...)
    for thousands of contacts.

    - the ones without data of their own are archived;
    - the ones with an e-mail of their own, and the archived ones, become
      aliases (type e-mail alias), the others keep their type, as they are real
      addresses;
    - a blank or copied name becomes the name of the main contact.
    """
    cr = env.cr
    cr.executemany(
        "UPDATE res_partner SET parent_id = %s WHERE id = %s",
        [(main_id, alias_id) for alias_id, main_id in main.items()],
    )
    alias_ids = tuple(redundant | with_email)
    if alias_ids:
        cr.execute(
            "UPDATE res_partner SET type = 'email_alias' WHERE id IN %s", (alias_ids,)
        )
    if redundant:
        cr.execute(
            "UPDATE res_partner SET active = false WHERE id IN %s", (tuple(redundant),)
        )
    _rename_like_main(env, main)


def _rename_like_main(env, main):
    """A blank or copied name of an alias becomes the name of its main contact.
    The name columns are copied with SQL, then the stored computed fields that
    depend on the name (complete name...) are recomputed, without any write."""
    cr = env.cr
    cr.execute("SELECT id, name FROM res_partner WHERE id IN %s", (tuple(main),))
    to_rename = [
        alias_id
        for alias_id, name in cr.fetchall()
        if not (name or "").strip() or COPY_NAME.search(name)
    ]
    if not to_rename:
        return
    copy_columns = SQL(", ").join(
        SQL("%s = m.%s", SQL.identifier(c), SQL.identifier(c))
        for c in sorted(_existing_columns(cr, ["name", "firstname", "lastname"]))
    )
    for alias_id in to_rename:
        cr.execute(
            SQL(
                "UPDATE res_partner a SET %s FROM res_partner m "
                "WHERE m.id = %s AND a.id = %s",
                copy_columns,
                main[alias_id],
                alias_id,
            )
        )
    env.invalidate_all()
    renamed = env["res.partner"].with_context(active_test=False).browse(to_rename)
    renamed.modified(["name"])
    env.flush_all()


# ----------------------------------------------------------------------------
# Move the relations of a contact to another one
# ----------------------------------------------------------------------------
def move_relations(cr, main):
    """Point every foreign key and reference of the partners (keys of ``main``)
    to their main contact (values). On a unique constraint, a row that only
    links the two (many2many table) is dropped when the main contact already has
    it, any other row stays on the partner. Both cases are logged."""
    if not main:
        return
    cr.execute("CREATE TEMPORARY TABLE t3642_alias (alias_id int, main_id int)")
    cr.executemany("INSERT INTO t3642_alias VALUES (%s, %s)", list(main.items()))
    cr.execute(
        """
        SELECT cl.relname, att.attname
        FROM pg_constraint con
        JOIN pg_class cl ON cl.oid = con.conrelid
        JOIN pg_attribute att ON att.attrelid = con.conrelid
                              AND att.attnum = con.conkey[1]
        WHERE con.contype = 'f' AND con.confrelid = 'res_partner'::regclass
        AND array_length(con.conkey, 1) = 1
        AND cl.relname NOT IN ('res_partner', 'interaction_resume')
        AND cl.relname NOT LIKE 'base_partner_merge_%'
        """
    )
    for table, column in cr.fetchall():
        _update(cr, table, column)
    # res_partner itself: commercial partner and the other children of an alias
    _update(cr, "res_partner", "commercial_partner_id")
    _update(cr, "res_partner", "parent_id")
    for table, model_col, id_col in REFERENCE_TABLES:
        _update(cr, table, id_col, model_col=model_col)
    cr.execute("DROP TABLE t3642_alias")


def _conditions(table, column, model_col=None):
    where = SQL("___t.%s = a.alias_id", SQL.identifier(column))
    if model_col:
        where = SQL("%s AND ___t.%s = 'res.partner'", where, SQL.identifier(model_col))
    if table == "res_partner":
        # Never make a contact its own parent
        where = SQL("%s AND ___t.id <> a.main_id", where)
    return where


def _is_link_table(cr, table):
    """A table that only links two records (many2many relation)."""
    cr.execute(
        "SELECT count(*) FROM information_schema.columns WHERE table_name = %s",
        (table,),
    )
    return cr.fetchone()[0] <= 2


def _update(cr, table, column, model_col=None):
    """Move the rows of ``table`` from the aliases to their main contact.
    ``model_col`` is set for tables that reference a record by (model, id)."""
    where = _conditions(table, column, model_col)
    try:
        with mute_logger("odoo.sql_db"), cr.savepoint():
            cr.execute(
                SQL(
                    "UPDATE %s ___t SET %s = a.main_id FROM t3642_alias a WHERE %s",
                    SQL.identifier(table),
                    SQL.identifier(column),
                    where,
                )
            )
        return
    except UniqueViolation:
        _logger.info("T3642: conflict on %s.%s, moving row by row", table, column)
    # Some rows are already on the main contact: go one by one
    link_table = _is_link_table(cr, table)
    dropped = kept = 0
    cr.execute("SELECT alias_id, main_id FROM t3642_alias")
    for alias_id, main_id in cr.fetchall():
        row_where = SQL("___t.%s = %s", SQL.identifier(column), alias_id)
        if model_col:
            row_where = SQL(
                "%s AND ___t.%s = 'res.partner'", row_where, SQL.identifier(model_col)
            )
        try:
            with mute_logger("odoo.sql_db"), cr.savepoint():
                cr.execute(
                    SQL(
                        "UPDATE %s ___t SET %s = %s WHERE %s",
                        SQL.identifier(table),
                        SQL.identifier(column),
                        main_id,
                        row_where,
                    )
                )
        except UniqueViolation:
            if link_table:
                cr.execute(
                    SQL(
                        "DELETE FROM %s ___t WHERE %s", SQL.identifier(table), row_where
                    )
                )
                dropped += cr.rowcount
            else:
                kept += 1
    if dropped:
        _logger.warning(
            "T3642: %s rows of %s.%s dropped, the main contact already has them",
            dropped,
            table,
            column,
        )
    if kept:
        _logger.warning(
            "T3642: %s rows of %s.%s kept on the alias, they conflict with a row of "
            "the main contact",
            kept,
            table,
            column,
        )


def reset_interactions(cr, partner_ids):
    """The interaction resume is built again at the next opening."""
    ids = tuple(set(partner_ids))
    if not ids:
        return
    cr.execute("SELECT to_regclass('interaction_resume')")
    if cr.fetchone()[0]:
        cr.execute("DELETE FROM interaction_resume WHERE partner_id IN %s", (ids,))
    if _existing_columns(cr, ["last_interaction_fetch_date"]):
        cr.execute(
            "UPDATE res_partner SET last_interaction_fetch_date = NULL, "
            "last_interaction_fetch_page = 0 WHERE id IN %s",
            (ids,),
        )


# ----------------------------------------------------------------------------
# Activities
# ----------------------------------------------------------------------------
def partner_link(partner):
    return Markup('<a href="#" data-oe-model="res.partner" data-oe-id="%s">%s</a>') % (
        partner.id,
        partner.display_name or partner.name or partner.id,
    )


def get_review_user(env):
    """User in charge of verifying the duplicated partners (setting of
    partner_auto_match), otherwise the first administrator."""
    value = env["ir.config_parameter"].sudo().get_param(REVIEW_USER_PARAM)
    user = env["res.users"].browse(int(value)).exists() if value else None
    return user or env["res.users"].search(
        [("groups_id", "in", env.ref("base.group_system").id)], order="id", limit=1
    )


def _get_activity_type(env):
    return env.ref(
        "partner_auto_match.activity_check_duplicates", raise_if_not_found=False
    ) or env.ref("mail.mail_activity_data_todo")


def schedule_review(env, partner, summary, lines):
    """Flag a partner for a manual review with a to-do activity (no e-mail sent).
    ``lines`` is a list of (partner, comment) shown in the note."""
    items = Markup("").join(
        Markup("<li>%s: %s</li>") % (partner_link(p), escape(comment))
        for p, comment in lines
    )
    env["mail.activity"].with_context(mail_activity_quick_update=True).create(
        {
            "res_model_id": env["ir.model"]._get_id("res.partner"),
            "res_id": partner.id,
            "activity_type_id": _get_activity_type(env).id,
            "summary": summary,
            "note": Markup("<ul>%s</ul>") % items,
            "date_deadline": fields.Date.today(),
            "user_id": get_review_user(env).id,
        }
    )
    _logger.warning(
        "T3642: review scheduled on partner %s: %s (%s)",
        partner.id,
        summary,
        "; ".join(f"{p.id}: {c}" for p, c in lines),
    )


# ----------------------------------------------------------------------------
# Merge
# ----------------------------------------------------------------------------
def fix_visitors(env, partner_ids):
    """Prepare the website visitors of the partners for the merge wizard of the
    website module: it casts the access token of the visitors of the destination
    partner to an integer, which fails for the visitors keeping a random token
    while linked to a partner. A partner can have several of them: merge them,
    then give the partner id as token, which is what the wizard expects."""
    if "website.visitor" not in env:
        return
    visitors = env["website.visitor"].sudo().with_context(active_test=False)
    for partner_id in partner_ids:
        partner_visitors = visitors.search(
            [("partner_id", "=", partner_id)], order="id"
        )
        for visitor in partner_visitors[1:]:
            visitor._merge_visitor(partner_visitors[0])
    # At most one visitor remains for each partner
    if not openupgrade.table_exists(env.cr, "website_visitor"):
        return
    env.cr.execute(
        """
        UPDATE website_visitor v SET access_token = v.partner_id::text
        WHERE v.partner_id IN %s AND v.access_token !~ '^[0-9]+$'
        AND NOT EXISTS (SELECT 1 FROM website_visitor w
                        WHERE w.access_token = v.partner_id::text)
        """,
        (tuple(partner_ids),),
    )
