# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models, fields, _

from openerp.addons.child_compassion.models.compassion_hold import HoldType


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
    sponsorships = fields.Integer('Registered sponsorships', readonly=True)
    effective_resupply = fields.Integer(
        compute='_compute_effective_resupply', store=True
    )

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

    @api.depends('sponsorships', 'holds')
    @api.multi
    def _compute_effective_resupply(self):
        for revision in self:
            revision.effective_resupply = revision.holds - \
                                          revision.sponsorships

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
        end_date = revision.week_end_date

        # Holds created in the period
        holds = self.env['compassion.hold'].search([
            ('create_date', '>=', start_date),
            ('create_date', '<=', end_date),
            ('type', '=', HoldType.CONSIGNMENT_HOLD.value)
        ])
        # Sponsorships created in the period
        sponsorships = self.env['recurring.contract'].search([
            ('type', '=', 'S'),
            ('start_date', '>=', start_date),
            ('start_date', '<=', end_date),
            ('state', '!=', 'cancelled'),
        ])
        if revision.type == 'web':
            nb_holds = len(holds.filtered(lambda h: h.channel == 'web'))
            nb_sponsorships = len(sponsorships.filtered(
                lambda s: s.channel == 'website' and
                s.origin_id.type not in ('partner', 'event', 'sub')))
        elif revision.type == 'ambassador':
            nb_holds = len(holds.filtered(
                lambda h: h.channel == 'ambassador'))
            nb_sponsorships = len(sponsorships.filtered(
                lambda s: s.origin_id.type == 'partner' and
                s.origin_id.partner_id))
        elif revision.type == 'events':
            nb_holds = len(holds.filtered(lambda h: h.channel == 'event'))
            nb_sponsorships = len(sponsorships.filtered(
                lambda s: s.origin_id.type == 'event'))
        elif revision.type == 'sub':
            nb_holds = self.env['compassion.hold'].search_count([
                ('create_date', '>=', start_date),
                ('create_date', '<=', end_date),
                ('type', '=', HoldType.SUB_CHILD_HOLD.value)
            ])
            nb_sponsorships = len(sponsorships.filtered(
                lambda s: s.origin_id.type == 'sub'))
        elif revision.type == 'cancel':
            nb_holds = 0
            nb_sponsorships = self.env['recurring.contract'].search_count([
                ('type', '=', 'S'),
                ('end_date', '>=', start_date),
                ('end_date', '<=', end_date),
                ('state', '=', 'terminated'),
                ('end_reason', '!=', '1'),
            ])

        revision.write({
            'holds': nb_holds,
            'sponsorships': nb_sponsorships,
        })
        return revision
