# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino. Copyright Compassion Suisse
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
##############################################################################

from openerp.osv import orm
import logging

logger = logging.getLogger(__name__)


class simple_recurring_contract(orm.Model):

    """ We add here creation of messages concerning commitments. """
    _inherit = "simple.recurring.contract"

    def _on_contract_active(self, cr, uid, ids, context=None):
        """ Create messages to GMC when new sponsorship is activated. """
        super(simple_recurring_contract, self)._on_contract_active(
            cr, uid, ids, context=context)
        message_obj = self.pool.get('gmc.message.pool')
        action_obj = self.pool.get('gmc.action')
        action_id = 0
        message_vals = {}

        for contract in self.browse(cr, uid, ids, context=context):
            if contract.child_id:
                # UpsertConstituent Message
                action_id = action_obj.search(
                    cr, uid, [('name', '=', 'UpsertConstituent')], limit=1, context=context)[0]
                message_vals = {
                    'action_id': action_id,
                    'object_id': contract.partner_id.id,
                    'partner_id': contract.partner_id.id,
                    'date': contract.first_payment_date,
                }
                message_obj.create(cr, uid, message_vals, context=context)

                # CreateCommitment Message
                action_id = action_obj.search(
                    cr, uid, [('name', '=', 'CreateCommitment')], limit=1, context=context)[0]
                message_vals.update({
                    'action_id': action_id,
                    'object_id': contract.id,
                    'child_id': contract.child_id.id,
                })
                message_obj.create(cr, uid, message_vals, context=context)

    def contract_terminated(self, cr, uid, ids, context=None):
        """ Inform GMC when sponsorship is terminated. """
        res = super(simple_recurring_contract, self).contract_terminated(
            cr, uid, ids)
        if res:
            message_obj = self.pool.get('gmc.message.pool')
            action_obj = self.pool.get('gmc.action')
            action_id = action_obj.search(
                cr, uid, [('name', '=', 'CancelCommitment')], limit=1, context=context)[0]
            message_vals = {'action_id': action_id}

            for contract in self.browse(cr, uid, ids, context=context):
                if contract.child_id:
                    message_vals.update({
                        'object_id': contract.id,
                        'partner_id': contract.partner_id.id,
                        'child_id': contract.child_id.id,
                    })
                    message_obj.create(cr, uid, message_vals)

        return res

    def _invoice_paid(self, cr, uid, invoice, context=None):
        """ Check if invoice paid contains
            a child gift and creates a message to GMC. """
        gift_product_names = [
            'Birthday Gift', 'General Gift', 'Family Gift',
            'Project Gift', 'Graduation Gift'
        ]
        message_obj = self.pool.get('gmc.message.pool')
        action_obj = self.pool.get('gmc.action')
        action_id = action_obj.search(
            cr, uid, [('name', '=', 'CreateGift')], limit=1, context=context)[0]
        message_vals = {
            'action_id': action_id,
            'date': invoice.date_invoice,
        }
        gift_ids = self.pool.get('product.product').search(
            cr, uid, [('name_template', 'in', gift_product_names)], context={'lang': 'en_US'})

        for invoice_line in invoice.invoice_line:
            if invoice_line.product_id.id in gift_ids:
                contract = invoice_line.contract_id
                if contract:
                    message_vals.update({
                        'object_id': invoice_line.id,
                        'partner_id': invoice_line.partner_id.id,
                        'child_id': contract.child_id.id,
                    })
                    message_obj.create(cr, uid, message_vals)
