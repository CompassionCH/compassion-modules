"""T3642 Clean the contacts that surfaced after the v14 to v18 migration.

In v14, partner_contact_in_several_companies hid the "attached" contacts from
the searches. They were migrated as children of type "other" of their main
contact and now show up as duplicates. They are e-mail aliases of their main
contact, so here we clean them. Nothing tells them apart from a real "Other
address" any more, but they keep the name of their main contact (blank, equal,
copied, or sharing a word under a person): the other children are not touched.

- every relation of the alias is moved to the main contact (communications,
  donations, requests, messages...), they are the same person;
- aliases that carry no information of their own (same or empty e-mail,
  address, phone numbers, birthdate) are archived;
- the aliases with an e-mail of their own are kept active, because incoming
  requests are matched on it. They, and the archived ones, get the type
  "email_alias", which the "Main contacts" filter hides from the contact lists;
- the other aliases (an address or a phone number of their own) stay of type
  "other", as they are real additional addresses;
- a partner that already had the type "email_alias" without a main contact
  becomes a normal contact;
- aliases that have a user or a sponsorship are left untouched and flagged
  with an activity on their main contact, for a manual review.
"""

import logging

from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api
from odoo.tools import SQL

from odoo.addons.crm_request.tools import partner_cleanup as cleanup

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    cleanup.fix_review_user_param(env)
    _fix_orphan_aliases(cr)
    aliases, skipped = _find_aliases(env)
    _flag_skipped(env, skipped)
    if not aliases:
        return
    # Some aliases are attached to another alias: go up to the main contact
    alias_ids = set(aliases.ids)
    main_contact = {a.id: _get_main_contact(a, alias_ids) for a in aliases}
    main = {alias_id: contact.id for alias_id, contact in main_contact.items()}
    redundant, with_email = cleanup.classify_aliases(cr, main)
    _logger.info(
        "T3642: %s migrated aliases to clean: %s without data of their own, %s with "
        "an e-mail of their own, %s with an address or a phone number only",
        len(aliases),
        len(redundant),
        len(with_email),
        len(aliases) - len(redundant) - len(with_email),
    )
    cleanup.move_relations(env, main)
    cleanup.apply_aliases(env, main, redundant, with_email)
    cleanup.reset_interactions(cr, set(main) | set(main.values()))


def _fix_orphan_aliases(cr):
    """An alias without main contact, in the databases where the type already
    existed (partner_compassion), is a contact like any other: the lists must not
    hide it."""
    cr.execute(
        "UPDATE res_partner SET type = 'contact' "
        "WHERE type = 'email_alias' AND parent_id IS NULL"
    )
    if cr.rowcount:
        _logger.info(
            "T3642: %s partners of type email_alias without parent set to contact",
            cr.rowcount,
        )


def _exists_sql(cr, table, condition):
    """EXISTS clause on a table of the sponsorship modules, which may be missing."""
    if not openupgrade.table_exists(cr, table):
        return SQL("false")
    return SQL(
        "EXISTS (SELECT 1 FROM %s x WHERE %s)", SQL.identifier(table), SQL(condition)
    )


def _find_aliases(env):
    """Children of type "other" that look like contacts attached in v14.
    :return: the ones to clean and, separately, the ones with a user or a
             sponsorship, which are left for a manual review."""
    cr = env.cr
    contract_condition = "x.partner_id = c.id"
    if openupgrade.column_exists(cr, "recurring_contract", "correspondent_id"):
        contract_condition += " OR x.correspondent_id = c.id"
    contract = _exists_sql(cr, "recurring_contract", contract_condition)
    group = _exists_sql(cr, "recurring_contract_group", "x.partner_id = c.id")
    cr.execute(
        SQL(
            """
            SELECT c.id, c.name, p.name, COALESCE(p.is_company, false),
                EXISTS (SELECT 1 FROM res_users u WHERE u.partner_id = c.id),
                %s, %s
            FROM res_partner c JOIN res_partner p ON p.id = c.parent_id
            WHERE c.type = 'other'
            """,
            contract,
            group,
        )
    )
    ids = []
    skipped = {}
    ignored = 0
    for partner_id, name, parent_name, parent_is_company, *usage in cr.fetchall():
        has_user, has_contract, has_group = usage
        if not cleanup.is_v14_alias(name, parent_name, parent_is_company):
            ignored += 1
        elif has_user or has_contract or has_group:
            reasons = []
            if has_user:
                reasons.append("linked to a user")
            if has_contract or has_group:
                reasons.append("linked to a sponsorship or a contract group")
            skipped[partner_id] = " and ".join(reasons)
        else:
            ids.append(partner_id)
    if ignored:
        _logger.info(
            "T3642: %s children of type other do not look like contacts attached in "
            "v14 (other name than their parent), they are left untouched",
            ignored,
        )
    partners = env["res.partner"].with_context(active_test=False)
    return partners.browse(ids), {partners.browse(k): v for k, v in skipped.items()}


def _flag_skipped(env, skipped):
    """Schedule an activity on the main contact of every skipped alias."""
    if skipped:
        _logger.warning(
            "T3642: %s contacts of type other left untouched (user or sponsorship), "
            "to review manually",
            len(skipped),
        )
    for alias, reason in skipped.items():
        main = alias.parent_id
        cleanup.schedule_review(
            env,
            main,
            "Review a secondary contact of this person",
            [(alias, f"secondary contact (type other) not cleaned: {reason}")],
        )


def _get_main_contact(alias, alias_ids):
    """The first parent of the alias that is not an alias to clean itself."""
    main = alias.parent_id
    seen = {alias.id}
    while main.id in alias_ids and main.id not in seen:
        seen.add(main.id)
        main = main.parent_id
    return main
