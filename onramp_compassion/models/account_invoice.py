# -*- coding: utf-8 -*-
#
#    Author: Yannick Vaucher
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from openerp import models, api

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSession

CREATE_INVOICE_KEYS = [
    'partner_id',
    'product_id',
    'amount',
]


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _delayed_create(self, data, eta=None):
        """ Create a job which will create the invoice later.

        param data: dict containing keys:
            ['partner_id', 'product_id', 'amount']
        """
        session = ConnectorSession.from_env(self.env)
        job_uuid = create_one_invoice.delay(session, self._name, data, eta=eta)
        return job_uuid

    @api.model
    def _create_single_line_invoice(self, data):
        """ Create an invoice with a single invoice_line

        It will play the onchanges and then validate the invoice.

        param data: dict containing keys:
            ['partner_id', 'product_id', 'amount']
        """
        partner_id = data.get('partner_id')
        product_id = data.get('product_id')

        invoice_line_model = self.env['account.invoice.line']

        inv_line_data = {
            'product_id': product_id,
        }
        onchange_product_data = invoice_line_model.product_id_change(
            product=product_id, uom_id=None, type='out_invoice',
            partner_id=partner_id
        )
        inv_line_data.update(onchange_product_data['value'])
        inv_line_data['price_unit'] = data.get('amount')

        inv_data = {
            'partner_id': partner_id,
            'invoice_line': [(0, 0, inv_line_data)],
        }
        onchange_partner_data = self.onchange_partner_id(
            'out_invoice', partner_id
        )
        inv_data.update(onchange_partner_data['value'])
        invoice = self.create(inv_data)
        # validate the invoice
        invoice.signal_workflow('invoice_open')
        return invoice


@job(default_channel='root.create_invoice')
def create_one_invoice(session, model_name, data):
    """Create an invoice."""
    session.env['account.invoice']._create_single_line_invoice(data)
