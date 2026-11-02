"""T3642 Merge the duplicated contacts.

Runs at the very end of the upgrade, after the aliases left by the v14
migration were cleaned (post-migration.py) and every module is loaded.

Duplicates are persons (active, without parent) found by one of these rules:
 1. same name and same e-mail
 2. same name and same zip
 3. same last name, first name and birthdate
 4. same name, zip and street

For each group, one contact is the main one: the only one with a user or an
active sponsorship, otherwise the one with the most invoices, then the oldest.
The other contacts are, depending on how they match the main one:
 - merged, in jobs as it is slow, if they are certainly the same person: same
   name and e-mail (1), same name and zip with an e-mail missing but not
   different (2), or rule 3 or 4 with the same e-mail;
 - otherwise turned into e-mail aliases (type "email_alias") of the main
   contact, with their relations moved to it, as for the aliases of the v14
   migration;
 - left as they are and flagged with an activity on the main contact if they
   are not directly matching it, or if several contacts have a user or an
   active sponsorship (never merged, never moved).
"""

import logging
from collections import defaultdict

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
    groups = _find_duplicate_groups(cr)
    to_merge = defaultdict(list)  # main contact id: duplicates to merge
    converted = {}
    flagged = []
    for group in groups:
        _process_group(env, group, to_merge, converted, flagged)
    _convert_to_children(env, converted)
    # The merges are slow: one job per main contact, merging its duplicates
    partners = env["res.partner"]
    for main_id, duplicate_ids in to_merge.items():
        partners.browse(main_id).with_delay_sh(
            "_merge_duplicates",
            duplicate_ids,
            channel="root.res_partner",
            identity_key=f"res.partner._merge_duplicates.{main_id}",
        )
    for dst, lines in flagged:
        cleanup.schedule_review(
            env, dst, "Review possible duplicates of this contact", lines
        )
    _logger.info(
        "T3642: %s groups of duplicates, %s contacts to merge (%s jobs), %s turned "
        "into children, %s flagged for review (%s activities)",
        len(groups),
        sum(len(ids) for ids in to_merge.values()),
        len(to_merge),
        len(converted),
        sum(len(lines) for _dst, lines in flagged),
        len(flagged),
    )


def _find_duplicate_groups(cr):
    """Groups (lists of partner dicts) of duplicates, linked by any rule."""

    def column(name):
        if openupgrade.column_exists(cr, "res_partner", name):
            return SQL.identifier(name)
        return SQL("NULL")

    cr.execute(
        SQL(
            """
            SELECT id, name, email, email_normalized, zip, street,
                %s AS firstname, %s AS lastname, %s AS birthdate
            FROM res_partner
            WHERE active AND parent_id IS NULL AND NOT COALESCE(is_company, false)
            AND COALESCE(name, '') <> ''
            """,
            column("firstname"),
            column("lastname"),
            column("birthdate_date"),
        )
    )
    partners = {}
    keys = defaultdict(list)
    for row in cr.dictfetchall():
        p = row
        p["name_key"] = " ".join(p["name"].lower().split())
        p["zip"] = (p["zip"] or "").strip()
        p["street"] = " ".join((p["street"] or "").lower().split())
        p["email_key"] = p["email_normalized"] or ""
        partners[p["id"]] = p
        if p["email_key"]:
            keys[("email", p["name_key"], p["email_key"])].append(p["id"])
        if p["zip"]:
            keys[("zip", p["name_key"], p["zip"])].append(p["id"])
        if p["birthdate"] and p["firstname"] and p["lastname"]:
            keys[
                (
                    "birth",
                    p["lastname"].strip().lower(),
                    p["firstname"].strip().lower(),
                    p["birthdate"],
                )
            ].append(p["id"])

    # Union-find on the partners sharing a key
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for ids in keys.values():
        for other in ids[1:]:
            parent[find(other)] = find(ids[0])
    clusters = defaultdict(list)
    for partner_id in list(parent):
        clusters[find(partner_id)].append(partner_id)
    groups = [
        [partners[i] for i in sorted(ids)] for ids in clusters.values() if len(ids) > 1
    ]
    _add_usage(cr, groups)
    return sorted(groups, key=lambda g: g[0]["id"])


def _add_usage(cr, groups):
    """Tell which contacts have a user, an active sponsorship, invoices."""
    ids = tuple(p["id"] for group in groups for p in group)
    if not ids:
        return
    usage = defaultdict(lambda: {"protected": [], "invoices": 0})
    cr.execute("SELECT partner_id FROM res_users WHERE partner_id IN %s", (ids,))
    for (pid,) in cr.fetchall():
        usage[pid]["protected"].append("a user")
    if openupgrade.table_exists(cr, "recurring_contract"):
        # Ended sponsorships do not matter: they are moved with the merge
        cr.execute(
            """
            SELECT DISTINCT pid FROM (
                SELECT partner_id AS pid FROM recurring_contract
                WHERE state NOT IN ('terminated', 'cancelled')
                UNION ALL SELECT correspondent_id FROM recurring_contract
                WHERE state NOT IN ('terminated', 'cancelled')
            ) c WHERE pid IN %s
            """,
            (ids,),
        )
        for (pid,) in cr.fetchall():
            usage[pid]["protected"].append("an active sponsorship")
    if openupgrade.table_exists(cr, "account_move"):
        cr.execute(
            "SELECT partner_id, count(*) FROM account_move "
            "WHERE partner_id IN %s AND move_type LIKE 'out_%%' GROUP BY 1",
            (ids,),
        )
        for pid, count in cr.fetchall():
            usage[pid]["invoices"] = count
    for group in groups:
        for p in group:
            p["protected"] = usage[p["id"]]["protected"]
            p["invoices"] = usage[p["id"]]["invoices"]


def _choose_main(group):
    """The main contact of the group, None if several have a user or an active
    sponsorship."""
    protected = [p for p in group if p["protected"]]
    if len(protected) > 1:
        return None
    if protected:
        return protected[0]
    return max(group, key=lambda p: (p["invoices"], -p["id"]))


def _relation(dst, src):
    """How the contact src matches the main contact dst.
    :return: "merge", "child", or None if they do not match directly."""
    same_name = dst["name_key"] == src["name_key"]
    same_email = bool(dst["email_key"]) and dst["email_key"] == src["email_key"]
    different_email = (
        bool(dst["email_key"]) and bool(src["email_key"]) and not same_email
    )
    same_zip = bool(dst["zip"]) and dst["zip"] == src["zip"]
    same_street = bool(dst["street"]) and dst["street"] == src["street"]
    same_birth = (
        bool(dst["birthdate"])
        and dst["birthdate"] == src["birthdate"]
        and (dst["lastname"] or "").strip().lower()
        == (src["lastname"] or "").strip().lower()
        and (dst["firstname"] or "").strip().lower()
        == (src["firstname"] or "").strip().lower()
        and bool(dst["lastname"])
        and bool(dst["firstname"])
    )
    if same_name and same_email:
        return "merge"
    if same_name and same_zip and not different_email:
        return "merge"
    if (same_birth or (same_name and same_zip and same_street)) and same_email:
        return "merge"
    if same_birth or (same_name and same_zip):
        return "child"
    return None


def _process_group(env, group, to_merge, converted, flagged):
    partners = env["res.partner"]
    dst_data = _choose_main(group)
    if not dst_data:
        # Several contacts with a user or an active sponsorship: nothing is touched
        main = partners.browse(group[0]["id"])
        flagged.append(
            (
                main,
                [
                    (
                        partners.browse(p["id"]),
                        _describe_usage(p),
                    )
                    for p in group
                ],
            )
        )
        return
    dst = partners.browse(dst_data["id"])
    lines = []
    for src_data in group:
        if src_data is dst_data:
            continue
        src = partners.browse(src_data["id"])
        relation = _relation(dst_data, src_data)
        if relation == "merge":
            to_merge[dst.id].append(src.id)
        elif relation == "child":
            converted[src.id] = dst.id
        else:
            lines.append(
                (src, "possible duplicate, not matching directly this contact")
            )
    if lines:
        flagged.append((dst, lines))


def _describe_usage(partner):
    """Why a duplicate is not touched."""
    if not partner["protected"]:
        return "possible duplicate, without user nor active sponsorship"
    # Remove the repetitions, keep the order
    return "possible duplicate, linked to " + " and ".join(
        dict.fromkeys(partner["protected"])
    )


def _convert_to_children(env, converted):
    """Turn the contacts in e-mail aliases of their main contact, as
    the aliases of the v14 migration: their relations go to the main contact."""
    if not converted:
        return
    cr = env.cr
    partners = env["res.partner"]
    cleanup.move_relations(cr, converted)
    env.invalidate_all()
    srcs = partners.browse(list(converted))
    cc_aliases = cleanup.get_cc_aliases(cr, srcs.ids)
    for src in srcs:
        dst = partners.browse(converted[src.id])
        redundant = cleanup.is_redundant(src, dst, cc_aliases)
        cr.execute(
            "UPDATE res_partner SET parent_id = %s, type = 'email_alias' WHERE id = %s",
            (dst.id, src.id),
        )
        env.invalidate_all()
        if src.name != dst.name:
            src.name = dst.name
        if redundant:
            src.active = False
    cleanup.reset_interactions(cr, set(converted) | set(converted.values()))
