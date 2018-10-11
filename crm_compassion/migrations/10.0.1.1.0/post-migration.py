# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.fields import Date
from odoo.addons.child_compassion.models.compassion_hold import HoldType


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Add sub channel to holds
    env.cr.execute("""
        UPDATE compassion_hold
        SET channel = 'sub'
        WHERE source_code = 'sub_proposal';
    """)
    # Sponsor cancel holds are never created by admin
    sponsor_cancel_holds = env['compassion.hold'].search([
        ('channel', '=', False),
        ('primary_owner', '!=', 1),
        '|', ('type', '=', HoldType.SPONSOR_CANCEL_HOLD.value),
        ('message_ids.body', 'like', 'Sponsor Cancel Hold')
    ])
    sponsor_cancel_holds.write({
        'channel': 'sponsor_cancel'
    })

    # FIX old weekly revision effective numbers
    env['demand.weekly.revision'].search([]).recompute_effective_numbers()

    last_prevision = env['demand.planning'].search([
        ('state', '=', 'draft')], limit=1)
    # Create the weekly revisions based on that prevision
    last_revision = env['demand.weekly.revision'].search(
        [], order='week_start_date desc', limit=1)
    last_revision_start = Date.from_string(last_revision.week_start_date)
    last_revision_end = Date.from_string(last_revision.week_end_date)
    today = date.today()
    while last_revision_end < today:
        last_revision_start += relativedelta(days=7)
        last_revision_end += relativedelta(days=7)
        last_week_demand = last_prevision.weekly_demand_ids.filtered(
            lambda w: w.week_start_date == Date.to_string(last_revision_start))
        if not last_week_demand:
            continue
        for type_tuple in last_revision.get_revision_types():
            revision_type = type_tuple[0]
            if revision_type == 'web':
                demand = last_week_demand.number_children_website
                resupply = last_week_demand.average_unsponsored_web
            elif revision_type == 'ambassador':
                demand = last_week_demand.number_children_ambassador
                resupply = last_week_demand.average_unsponsored_ambassador
            elif revision_type == 'events':
                demand = last_week_demand.number_children_events
                resupply = last_week_demand.resupply_events
            elif revision_type == 'sub':
                demand = last_week_demand.number_sub_sponsorship
                resupply = last_week_demand.resupply_sub
            elif revision_type == 'cancel':
                demand = 0
                resupply = last_week_demand.average_cancellation
            last_revision.create({
                'week_start_date': last_week_demand.week_start_date,
                'week_end_date': last_week_demand.week_end_date,
                'type': revision_type,
                'demand': demand,
                'resupply': resupply,
            })

    # Mark the pending demand planning as sent and generate next previsions.
    last_prevision.write({'state': 'sent'})
    last_prevision.process_weekly_demand()
