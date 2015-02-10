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

from openerp.osv import orm, fields
from openerp.tools.translate import _
from sponsorship_compassion.model.product import GIFT_TYPES
import logging

logger = logging.getLogger(__name__)


class recurring_contract(orm.Model):
    """ We add here creation of messages concerning commitments. """
    _inherit = "recurring.contract"

    _columns = {
        # Field to identify contracts modified by gmc.
        'gmc_state': fields.selection([
            ('biennial', _('Biennial')),
            ('depart', _('Child Departed')),
            ('transfer', _('Child Transfer')),
            ('suspension', _('Project Suspended'))], _('GMC State'))
    }

    def _on_contract_active(self, cr, uid, ids, context=None):
        """ Create messages to GMC when new sponsorship is activated. """
        super(recurring_contract, self)._on_contract_active(
            cr, uid, ids, context=context)
        message_obj = self.pool.get('gmc.message.pool')
        action_obj = self.pool.get('gmc.action')
        action_id = 0
        message_vals = {}

        if not isinstance(ids, list):
            ids = [ids]

        for contract in self.browse(cr, uid, ids, context=context):
            if contract.child_id:
                # UpsertConstituent Message
                action_id = action_obj.search(
                    cr, uid, [('name', '=', 'UpsertConstituent')],
                    limit=1, context=context)[0]
                message_vals = {
                    'action_id': action_id,
                    'object_id': contract.correspondant_id.id,
                    'partner_id': contract.correspondant_id.id,
                    'date': contract.activation_date,
                }
                message_obj.create(cr, uid, message_vals, context=context)

                # CreateCommitment Message
                action_id = action_obj.search(
                    cr, uid, [('name', '=', 'CreateCommitment')],
                    limit=1, context=context)[0]
                message_vals.update({
                    'action_id': action_id,
                    'object_id': contract.id,
                    'child_id': contract.child_id.id,
                })
                message_obj.create(cr, uid, message_vals, context=context)

    def contract_terminated(self, cr, uid, ids, context=None):
        """ Inform GMC when sponsorship is terminated,
        if end reason is from sponsor.
        """
        res = super(recurring_contract, self).contract_terminated(
            cr, uid, ids, context)
        if res:
            message_obj = self.pool.get('gmc.message.pool')
            action_obj = self.pool.get('gmc.action')
            action_id = action_obj.search(
                cr, uid, [('name', '=', 'CancelCommitment')],
                limit=1, context=context)[0]
            message_vals = {'action_id': action_id}

            for contract in self.browse(cr, uid, ids, context=context):
                # Contract must have child and not terminated by child or by
                # partner move
                end_reason = int(contract.end_reason)
                if contract.child_id and end_reason not in (1, 4):
                    message_vals.update({
                        'object_id': contract.id,
                        'partner_id': contract.correspondant_id.id,
                        'child_id': contract.child_id.id,
                    })
                    message_obj.create(cr, uid, message_vals)

        return res

    def _invoice_paid(self, cr, uid, invoice, context=None):
        """ Check if invoice paid contains
            a child gift and creates a message to GMC. """
        super(recurring_contract, self)._invoice_paid(cr, uid, invoice,
                                                      context)
        message_obj = self.pool.get('gmc.message.pool')
        action_obj = self.pool.get('gmc.action')
        action_id = action_obj.search(
            cr, uid, [('name', '=', 'CreateGift')], limit=1,
            context=context)[0]
        message_vals = {
            'action_id': action_id,
            'date': invoice.date_invoice,
        }
        gift_ids = self.pool.get('product.product').search(
            cr, uid, [('name_template', 'in', GIFT_TYPES)],
            context={'lang': 'en_US'})

        for invoice_line in invoice.invoice_line:
            contract = invoice_line.contract_id
            if invoice_line.product_id.id in gift_ids and contract:
                if invoice.payment_ids:
                    message_vals.update({
                        'object_id': invoice_line.id,
                        'partner_id': contract.correspondant_id.id,
                        'child_id': contract.child_id.id,
                    })
                    message_obj.create(cr, uid, message_vals)
                else:
                    # Invoice goes from paid to open state ->
                    # delete CreateGift message
                    mess_ids = message_obj.search(cr, uid, [
                        ('action_id', '=', action_id),
                        ('date', '=', invoice.date_invoice),
                        ('state', '=', 'new')], context=context)
                    message_obj.unlink(cr, uid, mess_ids, context)
