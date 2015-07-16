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

from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime

# Countries available for the child transfer
IP_COUNTRIES = ['AU', 'CA', 'DE', 'ES', 'FR', 'GB', 'IT', 'KR', 'NL',
                'NZ', 'US', 'NO']


class child_depart_wizard(models.TransientModel):
    _name = 'child.depart.wizard'

    end_date = fields.Date(
        required=True, default=datetime.today().strftime(DF))
    child_id = fields.Many2one(
        'compassion.child', 'Child',
        default=lambda self: self._get_child_id())
    transfer_country_id = fields.Many2one(
        'res.country', 'Country', domain=[('code', 'in', IP_COUNTRIES)])
    gp_exit_reason = fields.Selection(
        '_get_exit_reason', 'Exit reason', required=True)

    @api.model
    def _get_child_id(self):
        # Retrieve the id of the child from context
        return self.env.context.get('active_id', False)

    @api.model
    def _get_exit_reason(self):
        res = self.pool.get('compassion.child').get_gp_exit_reasons()
        res.append(('transfer', _('Transfer')))
        return res

    @api.multi
    def child_depart(self):
        self.ensure_one()
        vals = {'exit_date': self.end_date,
                'state': 'F'}

        # Child transfer
        if self.gp_exit_reason == 'transfer':
            vals['transfer_country_id'] = self.transfer_country_id.id
        # Other reasons
        else:
            vals['gp_exit_reason'] = self.gp_exit_reason

        self.child_id.write(vals)

        return True
