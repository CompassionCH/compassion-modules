"""T3642 Clean the contacts that surfaced after the v14 to v18 migration.

In v14, partner_contact_in_several_companies hid the "attached" contacts from
the searches. They were migrated as children of type "other" of their main
contact and now show up as duplicates. They are e-mail aliases of their main
contact, so here we clean them:

- every relation of the alias is moved to the main contact (communications,
  donations, requests, messages...), they are the same person;
- aliases that carry no information of their own (same or empty e-mail and
  address) are archived;
- the others are kept active with their e-mail address, because incoming
  requests are matched on it. They stay of type "other" and are hidden by
  the "Main contacts" filter;
- aliases that have a user or a sponsorship are left untouched for a manual
  review.
"""

import logging

from psycopg2 import Error as PsycopgError

from odoo import SUPERUSER_ID, api
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


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    aliases = _find_aliases(env)
    if not aliases:
        return
    # Some aliases are attached to another alias: go up to the main contact
    main_contact = {a.id: _get_main_contact(a, set(aliases.ids)) for a in aliases}
    main = {alias_id: contact.id for alias_id, contact in main_contact.items()}
    cc_aliases = _get_cc_aliases(cr, aliases.ids)
    redundant = aliases.filtered(
        lambda a: _is_redundant(a, main_contact[a.id], cc_aliases)
    )
    _logger.info(
        "T3642: %s migrated aliases to clean, %s of them carry no data of their own",
        len(aliases),
        len(redundant),
    )

    _move_relations(cr, main)

    # Attach every alias directly to its main contact
    for alias in aliases.filtered(lambda a: a.parent_id.id != main[a.id]):
        cr.execute(
            "UPDATE res_partner SET parent_id = %s WHERE id = %s",
            (main[alias.id], alias.id),
        )
    env.invalidate_all()
    redundant.write({"active": False})
    # The name of an alias is the one of its main contact
    for alias in aliases:
        if alias.name != main_contact[alias.id].name:
            alias.name = main_contact[alias.id].name
    # The interaction resume is built again at the next opening
    cr.execute(
        "DELETE FROM interaction_resume WHERE partner_id IN %s",
        (tuple(set(main) | set(main.values())),),
    )
    cr.execute(
        "UPDATE res_partner SET last_interaction_fetch_date = NULL, "
        "last_interaction_fetch_page = 0 WHERE id IN %s",
        (tuple(set(main) | set(main.values())),),
    )


def _find_aliases(env):
    """Children of type "other", migrated from attached contacts, to clean.
    The ones with a user or a sponsorship are left for a manual review."""
    cr = env.cr
    cr.execute(
        """
        SELECT c.id FROM res_partner c
        WHERE c.type = 'other' AND c.parent_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM res_users u WHERE u.partner_id = c.id)
        AND NOT EXISTS (SELECT 1 FROM recurring_contract r
                        WHERE r.partner_id = c.id OR r.correspondent_id = c.id)
        AND NOT EXISTS (SELECT 1 FROM recurring_contract_group g
                        WHERE g.partner_id = c.id)
        """
    )
    ids = [row[0] for row in cr.fetchall()]
    cr.execute(
        """
        SELECT count(*) FROM res_partner c
        WHERE c.type = 'other' AND c.parent_id IS NOT NULL
        """
    )
    skipped = cr.fetchone()[0] - len(ids)
    if skipped:
        _logger.warning(
            "T3642: %s contacts of type other left untouched (user or sponsorship), "
            "to review manually",
            skipped,
        )
    return env["res.partner"].with_context(active_test=False).browse(ids)


def _get_cc_aliases(cr, alias_ids):
    """Ids of the aliases that receive a copy of the e-mails of the main contact.
    The field is defined in partner_compassion, not loaded yet at this stage."""
    cr.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'res_partner' AND column_name = 'email_copy'"
    )
    if not cr.fetchone():
        return set()
    cr.execute(
        "SELECT id FROM res_partner WHERE email_copy AND id IN %s",
        (tuple(alias_ids),),
    )
    return {row[0] for row in cr.fetchall()}


def _get_main_contact(alias, alias_ids):
    """The first parent of the alias that is not an alias to clean itself."""
    main = alias.parent_id
    seen = {alias.id}
    while main.id in alias_ids and main.id not in seen:
        seen.add(main.id)
        main = main.parent_id
    return main


def _is_redundant(alias, main, cc_aliases):
    """No e-mail, address or CC of its own, compared to the main contact."""
    own_email = alias.email and (
        email_normalize(alias.email) != email_normalize(main.email)
    )
    own_address = alias.street and (
        alias.street != main.street or alias.zip != main.zip
    )
    return not (own_email or own_address or alias.id in cc_aliases)


def _move_relations(cr, main):
    """Point every foreign key and reference to the aliases to the main contact.
    Rows that would violate a unique constraint are dropped, like the partner
    merge wizard does."""
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
    # res_partner itself: children of the aliases and commercial partner
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
