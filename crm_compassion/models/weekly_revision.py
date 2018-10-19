# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _
from odoo.fields import Datetime

from odoo.addons.child_compassion.models.compassion_hold import HoldType


class WeeklyRevision(models.Model):
    _name = 'demand.weekly.revision'
    _description = 'Weekly Revision'
    _rec_name = 'week_start_date'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    week_start_date = fields.Date(required=True)
    week_end_date = fields.Date(required=True)
    type = fields.Selection('get_revision_types', required=True)

    demand = fields.Float('Demand prevision')
    resupply = fields.Float('Resupply prevision')
    holds = fields.Integer('Holds requested', readonly=True)
    effective_resupply = fields.Integer()

    _sql_constraints = [
        ('unique_week_type', "unique(week_start_date,type)",
         "Weekly revision already exist!")
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def get_revision_types(self):
        return [
            ('web', _('Web')),
            ('ambassador', _('Ambassador')),
            ('events', _('Events')),
            ('sub', _('Sub')),
            ('cancel', _('Cancellation')),
        ]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Compute all results. """
        start_date = vals['week_start_date']
        revision = self.search([
            ('week_start_date', '=', start_date),
            ('type', '=', vals['type'])
        ], limit=1)
        if revision:
            return revision

        revision = super(WeeklyRevision, self).create(vals)
        revision.recompute_effective_numbers()
        return revision

    def recompute_effective_numbers(self):
        for revision in self:
            start_date = revision.week_start_date
            end_date = revision.week_end_date

            # Holds created in the period
            demand_search = [
                ('create_date', '>=', start_date),
                ('create_date', '<=', end_date),
            ]
            resupply_search = [
                ('expiration_date', '>=', start_date),
                ('expiration_date', '<=', end_date),
            ]
            if revision.type == 'web':
                demand_search.append(('channel', '=', 'web'))
                resupply_search.append(('channel', '=', 'web'))
            elif revision.type == 'ambassador':
                demand_search.append(('channel', '=', 'ambassador'))
                resupply_search.append(('channel', '=', 'ambassador'))
            elif revision.type == 'events':
                demand_search.append(('channel', '=', 'event'))
                resupply_search.append(('channel', '=', 'event'))
            elif revision.type == 'sub':
                demand_search.append(('channel', '=', 'sub'))
                resupply_search.append(('channel', '=', 'sub'))
            elif revision.type == 'cancel':
                # This is a special case where we have no holds requested
                # and only resupply by sponsorships cancelled.
                cancellations = self.env['recurring.contract'].search([
                    ('type', 'like', 'S'),
                    ('state', '=', 'terminated'),
                    ('end_date', '>=', start_date),
                    ('end_date', '<=', end_date),
                    ('end_date', '!=', False),
                    ('hold_expiration_date', '!=', False),
                    ('end_reason', '!=', '1'),
                ])
                # Cancellations for which we didn't keep the child on hold
                resupply = len(cancellations.filtered(lambda c: (
                    Datetime.from_string(c.hold_expiration_date) -
                    Datetime.from_string(c.end_date)).total_seconds() < 60
                ))
                # Sponsor Cancel Holds that were released
                resupply_search.extend([
                    ('channel', '=', 'sponsor_cancel'),
                    ('type', '=', HoldType.SPONSOR_CANCEL_HOLD.value),
                ])
                resupply += self.env['compassion.hold'].search_count(
                    resupply_search)
                revision.effective_resupply = resupply
                continue

            hold_obj = self.env['compassion.hold']
            nb_holds = hold_obj.search_count(demand_search)
            resupply = hold_obj.search_count(resupply_search)
            revision.write({
                'holds': nb_holds,
                'effective_resupply': resupply,
            })
        return True
