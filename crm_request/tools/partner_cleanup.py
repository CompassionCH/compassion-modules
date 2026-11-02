"""Helpers shared by the migrations that clean the duplicated contacts (T3642)."""

import logging

from markupsafe import Markup, escape
from openupgradelib import openupgrade
from psycopg2 import Error as PsycopgError

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


def get_cc_aliases(cr, partner_ids):
    """Ids, among the given ones, of the partners that receive a copy of the
    e-mails of their main contact. The field is defined in partner_compassion,
    which may not be installed or loaded at this stage."""
    cr.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'res_partner' AND column_name = 'email_copy'"
    )
    if not cr.fetchone() or not partner_ids:
        return set()
    cr.execute(
        "SELECT id FROM res_partner WHERE email_copy AND id IN %s",
        (tuple(partner_ids),),
    )
    return {row[0] for row in cr.fetchall()}


def is_redundant(alias, main, cc_aliases):
    """No e-mail, address or CC of its own, compared to the main contact."""
    own_email = alias.email and (
        email_normalize(alias.email) != email_normalize(main.email)
    )
    own_address = alias.street and (
        alias.street != main.street or alias.zip != main.zip
    )
    return not (own_email or own_address or alias.id in cc_aliases)


def move_relations(cr, main):
    """Point every foreign key and reference of the partners (keys of ``main``)
    to their main contact (values). Rows that would violate a unique constraint
    are dropped, like the partner merge wizard does."""
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
    relations = cr.fetchall()
    # res_partner itself: commercial partner
    relations += [("res_partner", "commercial_partner_id")]
    for table, column in relations:
        _update(cr, table, column, "alias_id", "main_id")
    for table, model_col, id_col in REFERENCE_TABLES:
        _update(cr, table, id_col, "alias_id", "main_id", model_col=model_col)
    cr.execute("DROP TABLE t3642_alias")


def _update(cr, table, column, src, dst, model_col=None):
    """Move the rows of ``table`` from the aliases to their main contact.
    ``model_col`` is set for tables that reference a record by (model, id)."""
    where = SQL("___t.%s = a.%s", SQL.identifier(column), SQL.identifier(src))
    if model_col:
        where = SQL("%s AND ___t.%s = 'res.partner'", where, SQL.identifier(model_col))
    query = SQL(
        "UPDATE %s ___t SET %s = a.%s FROM t3642_alias a WHERE %s",
        SQL.identifier(table),
        SQL.identifier(column),
        SQL.identifier(dst),
        where,
    )
    try:
        with mute_logger("odoo.sql_db"), cr.savepoint():
            cr.execute(query)
    except PsycopgError:
        # A unique constraint is violated for some rows: go one by one and
        # drop the ones that already exist on the main contact.
        cr.execute("SELECT alias_id, main_id FROM t3642_alias")
        for alias_id, main_id in cr.fetchall():
            row_where = SQL("___t.%s = %s", SQL.identifier(column), alias_id)
            if model_col:
                row_where = SQL(
                    "%s AND ___t.%s = 'res.partner'",
                    row_where,
                    SQL.identifier(model_col),
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
            except PsycopgError:
                cr.execute(
                    SQL(
                        "DELETE FROM %s ___t WHERE %s",
                        SQL.identifier(table),
                        row_where,
                    )
                )


def reset_interactions(cr, partner_ids):
    """The interaction resume is built again at the next opening."""
    ids = tuple(set(partner_ids))
    if not ids:
        return
    cr.execute("SELECT to_regclass('interaction_resume')")
    if cr.fetchone()[0]:
        cr.execute("DELETE FROM interaction_resume WHERE partner_id IN %s", (ids,))
    cr.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name = 'res_partner' "
        "AND column_name = 'last_interaction_fetch_date'"
    )
    if cr.fetchone():
        cr.execute(
            "UPDATE res_partner SET last_interaction_fetch_date = NULL, "
            "last_interaction_fetch_page = 0 WHERE id IN %s",
            (ids,),
        )


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


def fix_visitor_tokens(cr, partner_ids):
    """The merge wizard of website casts the access token of the visitors of
    the destination partner to an integer, which fails for the visitors keeping
    a random token while linked to a partner. The token of a partner visitor is
    the id of the partner."""
    if not openupgrade.table_exists(cr, "website_visitor"):
        return
    cr.execute(
        """
        UPDATE website_visitor v SET access_token = v.partner_id::text
        WHERE v.partner_id IN %s AND v.access_token !~ '^[0-9]+$'
        AND NOT EXISTS (SELECT 1 FROM website_visitor w
                        WHERE w.access_token = v.partner_id::text)
        """,
        (tuple(partner_ids),),
    )
