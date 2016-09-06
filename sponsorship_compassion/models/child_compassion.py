# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields

import logging

logger = logging.getLogger(__name__)


class ChildCompassion(models.Model):
    _inherit = 'compassion.child'

    sponsorship_ids = fields.One2many(
        'recurring.contract', compute='_set_related_contracts',
        string="Sponsorships", readonly=True)

    @api.multi
    def _set_related_contracts(self):
        con_obj = self.env['recurring.contract']
        for child in self:
            child.sponsorship_ids = con_obj.search([
                ('child_id', '=', child.id),
                ('type', '=', 'S')])

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
