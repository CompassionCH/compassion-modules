# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from dateutil.relativedelta import relativedelta

from odoo import fields
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Find SUB sponsorships without parent and try to attach them
    contract_obj = env['recurring.contract']
    orphans = contract_obj.search([
        ('origin_id.type', '=', 'sub'),
        ('parent_id', '=', False)
    ])
    for sponsorship in orphans:
        start_date = sponsorship.start_date
        one_month_before = fields.Date.to_string(fields.Date.from_string(
            start_date) - relativedelta(months=1))
        partners = sponsorship.partner_id | sponsorship.correspondant_id
        candidates = contract_obj.search([
            '|', ('partner_id', 'in', partners.ids),
            ('correspondant_id', 'in', partners.ids),
            ('state', '=', 'terminated'),
            ('end_date', '<', start_date),
            ('end_date', '>', one_month_before)
        ])
        if len(candidates) == 1:
            env.cr.execute(
                "UPDATE recurring_contract "
                "SET parent_id = %s "
                "WHERE id = %s",
                [candidates.id, sponsorship.id]
            )

    # Migrate SUB Sponsorship origins : take the origin from parent
    subs = contract_obj.search([
        ('origin_id.type', '=', 'sub'),
        ('parent_id', '!=', False)
    ])
    for sponsorship in subs:
        root_origin = sponsorship
        to_change = sponsorship
        while root_origin.origin_id.type == 'sub' and root_origin.parent_id:
            to_change |= root_origin
            root_origin = root_origin.parent_id
        if root_origin.origin_id.type != 'sub':
            env.cr.execute(
                "UPDATE recurring_contract "
                "SET origin_id = %s, channel = 'sub' "
                "WHERE id = ANY(%s)",
                [root_origin.origin_id.id, to_change.ids]
            )

    # Change type of SUB Sponsorship Origin
    sub_origin = env['recurring.contract.origin'].search([
        ('name', '=', 'SUB Sponsorship')
    ])
    sub_origin.write({'type': 'other'})
