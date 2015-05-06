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
import logging

logger = logging.getLogger(__name__)


class recurring_contract(orm.Model):
    """ We add here creation of messages concerning commitments. """
    _inherit = "recurring.contract"

    def _get_gmc_states(self, cr, uid, context=None):
        """ Overridable method to get GMC states. """
        return [
            ('picture', _('New Picture')),
            ('casestudy', _('New Case Study')),
            ('biennial', _('Biennial')),
            ('depart', _('Child Departed')),
            ('transfer', _('Child Transfer'))]

    def __get_gmc_states(self, cr, uid, context=None):
        return self._get_gmc_states(cr, uid, context)

    _columns = {
        # Field to identify contracts modified by gmc.
        'gmc_state': fields.selection(__get_gmc_states, _('GMC State'))
    }

    def _on_contract_active(self, cr, uid, ids, context=None):
        """ Create messages to GMC when new sponsorship is activated. """
        super(recurring_contract, self)._on_contract_active(
            cr, uid, ids, context=context)
        message_obj = self.pool.get('gmc.message.pool')
        action_id = 0
        message_vals = {}

        if not isinstance(ids, list):
            ids = [ids]

        for contract in self.browse(cr, uid, ids, context=context):
            if contract.type == 'S':
                # UpsertConstituent Message
                action_id = self.get_action_id(cr, uid, 'UpsertConstituent')
                partner_id = contract.correspondant_id.id
                message_vals = {
                    'action_id': action_id,
                    'object_id': partner_id,
                    'partner_id': partner_id,
                }
                # Look if one Upsert is already pending for the same partner
                mess_ids = message_obj.search(cr, uid, [
                    ('action_id', '=', action_id),
                    ('partner_id', '=', partner_id),
                    ('state', '=', 'new')], context=context)
                if not mess_ids:
                    message_obj.create(cr, uid, message_vals, context=context)

                # CreateCommitment Message
                action_id = self.get_action_id(cr, uid, 'CreateCommitment')
                message_vals.update({
                    'action_id': action_id,
                    'object_id': contract.id,
                    'child_id': contract.child_id.id,
                })
                message_obj.create(cr, uid, message_vals, context)

    def contract_terminated(self, cr, uid, ids, context=None):
        """ Inform GMC when sponsorship is terminated.
        Send pending gifts if any are waiting.
        """
        if context is None:
            context = dict()
        res = super(recurring_contract, self).contract_terminated(
            cr, uid, ids, context)
        if res:
            message_obj = self.pool.get('gmc.message.pool')
            action_id = self.get_action_id(cr, uid, 'CancelCommitment')
            message_vals = {'action_id': action_id}

            for contract in self.browse(cr, uid, ids, context=context):
                end_reason = int(contract.end_reason)
                if contract.type == 'S' and end_reason != 1:
                    # Send pending gifts
                    mess_ids = message_obj.search(cr, uid, [
                        ('action_id', '=', self.get_action_id(cr, uid,
                                                              'CreateGift')),
                        ('state', '=', 'new'),
                        ('partner_id', '=', contract.correspondant_id.id),
                        ('child_id', '=', contract.child_id.id)],
                        context=context)
                    context['force_send'] = True
                    message_obj.process_messages(cr, uid, mess_ids, context)
                # Contract must have child and not terminated by
                # partner move
                if contract.type == 'S' and end_reason != 4:
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
        action_id = self.get_action_id(cr, uid, 'CreateGift')
        message_vals = {
            'action_id': action_id,
            'date': invoice.date_invoice,
        }
        gift_ids = self.pool.get('product.product').search(
            cr, uid, [('type', '=', 'G')],
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
                    ('state', 'in', ['success', 'fondue']),
                    ('action_id', '=', action_id)], context=context)
                if mess_ids:
                    raise orm.except_orm(
                        _("Unreconcile error"),
                        _("You are not allowed to unreconcile this invoice. "
                          "The Gift was already sent to GMC ! "))

                # 2. Delete pending CreateGift and CreateCommitment messages
                self._clean_messages(cr, uid, invoice_line.id, context)

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

    def _filter_clean_invoices(self, cr, uid, ids, since_date=None,
                               to_date=None, context=None):
        """ Don't clean invoice lines related to GIFT messages sent to GMC.
        Delete pending messages. """
        message_obj = self.pool.get('gmc.message.pool')
        sender_ids = [c.correspondant_id.id for c in self.browse(cr, uid, ids,
                                                                 context)]
        mess_ids = message_obj.search(cr, uid, [
            ('action_id', '=', self.get_action_id(cr, uid, 'CreateGift')),
            ('partner_id', 'in', sender_ids),
            ('state', 'not in', ['new', 'failure'])], context=context)
        filter_invl_ids = [m.object_id for m in message_obj.browse(
            cr, uid, mess_ids, context)]

        invl_filter = super(recurring_contract, self)._filter_clean_invoices(
            cr, uid, ids, since_date, to_date, context)
        invl_filter.append(('id', 'not in', filter_invl_ids))
        return invl_filter

    def get_action_id(self, cr, uid, name, context=None):
        return self.pool.get('gmc.action').get_action_id(cr, uid, name,
                                                         context)

    def new_biennial(self, cr, uid, ids, context=None):
        """ Called when new picture and new case study is available. """
        self.write(cr, uid, ids, {'gmc_state': 'biennial'}, context)

    def set_gmc_event(self, cr, uid, ids, event, context=None):
        """
        Called when a Child Update was received for a sponsored child.
        Arg event can have one of the following values :
            - Transfer : child was transferred to another project
            - CaseStudy : child has a new casestudy
            - NewImage : child has a new image
        """
        # Maps the event to the gmc state value of contract
        gmc_states = {
            'Transfer': 'transfer',
            'CaseStudy': 'casestudy',
            'NewImage': 'picture',
        }
        res = True
        for contract in self.browse(cr, uid, ids, context):
            if not (contract.gmc_state == 'biennial' and
                    event in ('CaseStudy', 'NewImage')):
                res = res and contract.write({'gmc_state': gmc_states[event]})
        return res
