# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields

import logging

logger = logging.getLogger(__name__)


class ChildCompassion(models.Model):
    _inherit = 'compassion.child'

    sponsorship_ids = fields.One2many(
        'recurring.contract', compute='_compute_related_contracts',
        string="Sponsorships", readonly=True)
    has_been_sponsored = fields.Boolean(compute='_compute_has_been_sponsored')

    @api.multi
    def _compute_has_been_sponsored(self):
        for child in self:
            child.has_been_sponsored = child.sponsorship_ids

    @api.multi
    def _compute_related_contracts(self):
        con_obj = self.env['recurring.contract']
        for child in self:
            child.sponsorship_ids = con_obj.search([
                ('child_id', '=', child.id),
                ('type', 'like', 'S')])

    def depart(self):
        """ End the sponsorship. """
        for child in self.filtered('sponsor_id'):
            sponsorship = child.sponsorship_ids[0]
            sponsorship.with_context(default_type='S').write({
                'end_reason': '1',  # Child departure
                'end_date': fields.Date.today(),
            })
            sponsorship.signal_workflow('contract_terminated')
        super(ChildCompassion, self).depart()

    @api.multi
    def child_released(self):
        """
        Cancel waiting sponsorships when child is released:
        the sponsor never paid and hold is expired.
        :return: True
        """
        res = super(ChildCompassion, self).child_released()
        waiting_sponsorships = self.mapped('sponsorship_ids').filtered(
            lambda s: s.state in ('draft', 'waiting', 'waiting_payment'))
        waiting_sponsorships.with_context(default_type='S').write({
            'end_reason': '9',  # Never Paid
            'end_date': fields.Date.today(),
        })
        waiting_sponsorships.signal_workflow('contract_terminated')
        return res
