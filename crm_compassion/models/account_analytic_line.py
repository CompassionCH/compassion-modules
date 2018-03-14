# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class AnalyticAccount(models.Model):
    """ Add year in name of analytic accounts. """
    _inherit = 'account.analytic.account'

    year = fields.Char()
    event_id = fields.Many2one(
        'crm.event.compassion', 'Event',
        # Only used to set by default the event at migration
        # TODO Remove compute when this in production
        compute='_compute_event', store=True, readonly=True)

    @api.multi
    def _compute_event(self):
        for account in self:
            account.event_id = self.env['crm.event.compassion'].search([
                ('analytic_id', '=', account.id)
            ], limit=1)

    @api.multi
    def name_get(self):
        res = []
        for analytic in self:
            name = analytic.name
            if analytic.code:
                name = '[' + analytic.code + '] ' + name
            if analytic.year and not name.endswith(analytic.year):
                name = name + ' ' + analytic.year
            res.append((analytic.id, name))
        return res
