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

from openerp import netsvc
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
            ('picture', _('New Picture')),
            ('casestudy', _('New Case Study')),
            ('depart', _('Child Departed')),
            ('transfer', _('Child Transfer')),
            ('suspension', _('Project Fund-Suspended')),
            ('suspension-extension', _('Fund suspension extension')),
            ('reactivation', _('Project Reactivated'))], _('GMC State'))
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
                partner_id = contract.correspondant_id.id
                message_vals = {
                    'action_id': action_id,
                    'object_id': partner_id,
                    'partner_id': partner_id,
                    'date': contract.activation_date,
                }
                # Look if one Upsert is already pending for the same partner
                mess_ids = message_obj.search(cr, uid, [
                    ('action_id', '=', action_id),
                    ('partner_id', '=', partner_id),
                    ('state', '=', 'new')], context=context)
                if not mess_ids:
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
                message_obj.create(cr, uid, message_vals, context)

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
                # Contract must have child and not terminated by
                # partner move
                end_reason = int(contract.end_reason)
                if contract.child_id and end_reason != 4:
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
            if not contract:
                break
            if invoice_line.product_id.id in gift_ids and invoice.payment_ids:
                # CreateGift
                message_vals.update({
                    'object_id': invoice_line.id,
                    'partner_id': contract.correspondant_id.id,
                    'child_id': contract.child_id.id,
                })
                message_obj.create(cr, uid, message_vals)
            elif not invoice.payment_ids:
                # Invoice goes from paid to open state
                # 1. Check if a GIFT was sent to GMC and prevent unrec
                mess_ids = message_obj.search(cr, uid, [
                    ('invoice_line_id', '=', invoice_line.id),
                    ('state', '=', 'success'),
                    ('action_id', '=', action_id)], context=context)
                if mess_ids:
                    raise orm.except_orm(
                        _("Unreconcile error"),
                        _("You are not allowed to unreconcile this invoice. "
                          "The Gift was already sent to GMC ! "))

                # 2. Delete pending CreateGift and CreateCommitment messages
                self._clean_messages(cr, uid, invoice_line.id, context)

    def suspend_contract(self, cr, uid, ids, context=None,
                         date_start=None, date_end=None):
        """ Mark the state of contract when it is suspended. """
        self.write(cr, uid, ids, {'gmc_state': 'suspension'}, context)
        return super(recurring_contract, self).suspend_contract(
            cr, uid, ids, context, date_start, date_end)

    def _on_invoice_line_removal(self, cr, uid, invoice_lines, context=None):
        """ Removes the corresponding Affectats in GP.
            @param: invoice_lines (dict): {
                line_id: [invoice_id, child_code, product_name, amount]}
        """
        super(recurring_contract, self)._on_invoice_line_removal(
            cr, uid, invoice_lines, context)
        self._clean_messages(cr, uid, invoice_lines.keys(), context)

    def _clean_messages(self, cr, uid, invoice_line_ids, context=None):
        """ Removes the pending messages linked to an invoice line_id
        that was unreconciled. """
        if not isinstance(invoice_line_ids, list):
            invoice_line_ids = [invoice_line_ids]
        message_obj = self.pool.get('gmc.message.pool')
        wf_service = netsvc.LocalService('workflow')

        mess_ids = message_obj.search(cr, uid, [
            ('invoice_line_id', 'in', invoice_line_ids),
            ('state', 'in', ['new', 'failure'])], context=context)
        for message in message_obj.browse(cr, uid, mess_ids, context):
            if message.action_id.name == 'CreateCommitment':
                # We set back the sponsorship in waiting state
                wf_service.trg_validate(
                    uid, 'recurring.contract', message.object_id,
                    'contract_activation_cancelled', cr)
        message_obj.unlink(cr, uid, mess_ids, context)
