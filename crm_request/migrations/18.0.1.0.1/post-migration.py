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
- aliases that have a user or a sponsorship are left untouched and flagged
  with an activity on their main contact, for a manual review.
"""

import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.crm_request.tools import partner_cleanup as cleanup

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    cleanup.fix_review_user_param(env)
    aliases, skipped = _find_aliases(env)
    _flag_skipped(env, skipped)
    if not aliases:
        return
    # Some aliases are attached to another alias: go up to the main contact
    main_contact = {a.id: _get_main_contact(a, set(aliases.ids)) for a in aliases}
    main = {alias_id: contact.id for alias_id, contact in main_contact.items()}
    cc_aliases = cleanup.get_cc_aliases(cr, aliases.ids)
    redundant = aliases.filtered(
        lambda a: cleanup.is_redundant(a, main_contact[a.id], cc_aliases)
    )
    _logger.info(
        "T3642: %s migrated aliases to clean, %s of them carry no data of their own",
        len(aliases),
        len(redundant),
    )

    cleanup.move_relations(cr, main)

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
    cleanup.reset_interactions(cr, set(main) | set(main.values()))


def _find_aliases(env):
    """Children of type "other", migrated from attached contacts.
    :return: the ones to clean and, separately, the ones with a user or a
             sponsorship, which are left for a manual review."""
    cr = env.cr
    cr.execute(
        """
        SELECT c.id,
            EXISTS (SELECT 1 FROM res_users u WHERE u.partner_id = c.id),
            EXISTS (SELECT 1 FROM recurring_contract r
                    WHERE r.partner_id = c.id OR r.correspondent_id = c.id),
            EXISTS (SELECT 1 FROM recurring_contract_group g
                    WHERE g.partner_id = c.id)
        FROM res_partner c
        WHERE c.type = 'other' AND c.parent_id IS NOT NULL
        """
    )
    ids = []
    skipped = {}
    for partner_id, has_user, has_contract, has_group in cr.fetchall():
        if has_user or has_contract or has_group:
            reasons = []
            if has_user:
                reasons.append("linked to a user")
            if has_contract or has_group:
                reasons.append("linked to a sponsorship or a contract group")
            skipped[partner_id] = " and ".join(reasons)
        else:
            ids.append(partner_id)
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
