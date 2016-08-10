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
from openerp import api, models, fields


class WeeklyRevision(models.Model):
    _name = 'demand.weekly.revision'
    _description = 'Weekly Revision'
    _rec_name = 'week_start_date'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    week_start_date = fields.Date(required=True)
    week_end_date = fields.Date(required=True)

    # Demand fields
    web_demand = fields.Integer()
    ambassador_demand = fields.Integer()
    events_demand = fields.Integer()
    total_demand = fields.Integer()

    # Resupply fields
    web_resupply = fields.Float()
    ambassador_resupply = fields.Float()
    cancellation = fields.Float()
    events_resupply = fields.Integer()
    total_resupply = fields.Integer()

    # Results (how many sponsorships we made that week) vs
    # (how many holds we requested that week)
    web_sponsorships = fields.Integer(readonly=True)
    ambassador_sponsorships = fields.Integer(readonly=True)
    events_sponsorships = fields.Integer(readonly=True)
    cancellation_sponsorships = fields.Integer(readonly=True)
    total_sponsorships = fields.Integer(readonly=True)

    web_holds = fields.Integer(readonly=True)
    ambassador_holds = fields.Integer(readonly=True)
    events_holds = fields.Integer(readonly=True)
    total_holds = fields.Integer(readonly=True)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Compute all results. """
        revision = super(WeeklyRevision, self).create(vals)
        start_date = revision.week_start_date
        end_date = revision.week_end_date

        # Holds created in the period
        holds = self.env['compassion.hold'].search([
            ('create_date', '>=', start_date),
            ('create_date', '<=', end_date),
            ('type', '=', 'Consignment Hold')
        ])
        web_holds = len(holds.filtered(lambda h: h.channel == 'web'))
        ambassador_holds = len(holds.filtered(
            lambda h: h.channel == 'ambassador'))
        event_holds = len(holds.filtered(lambda h: h.channel == 'event'))

        # Sponsorships created in the period
        sponsorships = self.env['recurring.contract'].search([
            ('type', '=', 'S'),
            ('start_date', '>=', start_date),
            ('start_date', '<=', end_date),
            ('state', '!=', 'cancelled'),
        ])
        web_sponsorships = len(sponsorships.filtered(
            lambda s: s.channel == 'website'))
        ambassador_sponsorships = len(sponsorships.filtered(
            lambda s: s.origin_id.type == 'partner' and
            s.origin_id.partner_id))
        event_sponsorships = len(sponsorships.filtered(
            lambda s: s.origin_id.type == 'event'))
        cancel_sponsorships = self.env['recurring.contract'].search_count([
            ('type', '=', 'S'),
            ('end_date', '>=', start_date),
            ('end_date', '<=', end_date),
            ('state', '=', 'terminated'),
            ('end_reason', '!=', '1'),
        ])

        revision.write({
            'web_holds': web_holds,
            'ambassador_holds': ambassador_holds,
            'events_holds': event_holds,
            'total_holds': len(holds),
            'web_sponsorships': web_sponsorships,
            'ambassador_sponsorships': ambassador_sponsorships,
            'events_sponsorships': event_sponsorships,
            'cancellation_sponsorships': cancel_sponsorships,
            'total_sponsorships': len(sponsorships),
        })
        return revision
