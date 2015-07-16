# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, fields, models


class end_sponsorship_wizard(models.TransientModel):
    _inherit = 'end.contract.wizard'

    gp_exit_reason = fields.Selection(
        '_get_exit_reason', string='Exit reason')

    @api.multi
    def _get_exit_reason(self):
        return self.env['compassion.child'].get_gp_exit_reasons()

    @api.multi
    def end_contract(self):
        self.ensure_one()
        res = super(end_sponsorship_wizard, self).end_contract()

        if self.child_id and 'S' in self.contract_id.type:
            # If sponsor moves, the child may be transferred
            if self.do_transfer:
                self.child_id.write({
                    'state': 'F',
                    'transfer_country_id': self.transfer_country_id.id,
                    'exit_date': self.end_date})

            # If child has departed, write exit_details
            elif self.end_reason == '1':
                self.child_id.write({
                    'state': 'F',
                    'gp_exit_reason': self.gp_exit_reason,
                    'exit_date': self.end_date})
        return res
