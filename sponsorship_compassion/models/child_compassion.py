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

    @api.multi
    def child_released(self, state='R'):
        """
        Cancel waiting sponsorships when child is released:
        the sponsor never paid and hold is expired.
        :return: True
        """
        res = super().child_released(state)
        if state == 'F':
            # Departure
            depart = self.env.ref('sponsorship_compassion.end_reason_depart')
            for child in self.filtered('sponsor_id'):
                sponsorship = child.sponsorship_ids[0]
                sponsorship.end_reason_id = depart.id
                sponsorship.contract_terminated()
        else:
            # Hold expiration
            hold_released = self.env.ref(
                'sponsorship_compassion.end_reason_release')
            waiting_sponsorships = self.mapped('sponsorship_ids').filtered(
                lambda s: s.state in ('draft', 'waiting', 'waiting_payment'))
            if waiting_sponsorships:
                waiting_sponsorships.end_reason_id = hold_released
                waiting_sponsorships.contract_terminated()
        return res
