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

from openerp import api, models, fields, exceptions, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime
import logging

from openerp.addons.sponsorship_compassion.model.product import GIFT_CATEGORY

logger = logging.getLogger(__name__)


class recurring_contract(models.Model):
    """ We add here creation of messages concerning commitments. """
    _inherit = "recurring.contract"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    # Field to identify contracts modified by gmc.
    gmc_state = fields.Selection('_get_gmc_states', 'GMC State')
    cancel_gifts_on_termination = fields.Boolean(
        'Cancel pending gifts if sponsorship is terminated')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_gmc_states(self):
        """ Overridable method to get GMC states. """
        return [
            ('picture', _('New Picture')),
            ('casestudy', _('New Case Study')),
            ('biennial', _('Biennial')),
            ('depart', _('Child Departed')),
            ('transfer', _('Child Transfer'))]

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def invoice_paid(self, invoice):
        """ Check if invoice paid contains
            a child gift and creates a message to GMC. """
        super(recurring_contract, self).invoice_paid(invoice)
        message_obj = self.env['gmc.message.pool']
        action_id = self.get_action_id('CreateGift')

        for invoice_line in invoice.invoice_line:
            message_vals = {
                'action_id': action_id,
                'date': invoice.date_invoice,
            }
            contract = invoice_line.contract_id
            if contract:
                if invoice_line.product_id.categ_name == GIFT_CATEGORY:
                    # CreateGift
                    message_vals.update({
                        'object_id': invoice_line.id,
                    })
                    if contract.child_id.type == 'LDP':
                        message_vals.update({
                            'state': 'failure',
                            'failure_reason': 'Gift cannot be sent to LDP'
                        })
                    message_obj.create(message_vals)

    def invoice_unpaid(self, invoice):
        super(recurring_contract, self).invoice_unpaid(invoice)
        action_id = self.get_action_id('CreateGift')
        for invoice_line in invoice.invoice_line:
            # 1. Check if a GIFT was sent to GMC and prevent unreconcile.
            mess_count = self.env['gmc.message.pool'].search_count([
                ('invoice_line_id', '=', invoice_line.id),
                ('state', 'in', ['success', 'fondue']),
                ('action_id', '=', action_id)])
            if mess_count:
                raise exceptions.Warning(
                    _("Unreconcile error"),
                    _("You are not allowed to unreconcile this invoice. "
                      "The Gift was already sent to GMC ! "))

            # 2. Delete pending CreateGift and CreateCommitment messages
            self._clean_messages(invoice_line.id)

    def get_action_id(self, name):
        return self.env['gmc.action'].get_action_id(name)

    def new_biennial(self):
        """ Called when new picture and new case study is available. """
        self.write({'gmc_state': 'biennial'})

    @api.one
    def set_gmc_event(self, event):
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
        if not self.gmc_state == 'biennial' and event in (
                'CaseStudy', 'NewImage'):
            res = self.write({'gmc_state': gmc_states[event]})
        return res

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def reset_gmc_state(self):
        """ Useful for manually unset GMC State. """
        return self.write({'gmc_state': False})

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_active(self):
        """ Create messages to GMC when new sponsorship is activated. """
        super(recurring_contract, self).contract_active()
        message_obj = self.env['gmc.message.pool']
        action_id = 0
        message_vals = dict()

        for contract in self:
            if 'S' in contract.type:
                # UpsertConstituent Message
                action_id = self.get_action_id('UpsertConstituent')
                partner_id = contract.correspondant_id.id
                message_vals = {
                    'action_id': action_id,
                    'object_id': partner_id,
                }
                # Look if one Upsert is already pending for the same partner
                mess_count = message_obj.search_count([
                    ('action_id', '=', action_id),
                    ('partner_id', '=', partner_id),
                    ('state', '=', 'new')])
                if not mess_count:
                    message_obj.create(message_vals)

                # CreateCommitment Message
                action_id = self.get_action_id('CreateCommitment')
                message_vals.update({
                    'action_id': action_id,
                    'object_id': contract.id,
                })
                message_obj.create(message_vals)

    @api.multi
    def contract_terminated(self):
        """ Inform GMC when sponsorship is terminated.
        Send pending gifts if any are waiting.
        """
        res = super(recurring_contract, self).contract_terminated()
        if res:
            message_obj = self.env['gmc.message.pool'].with_context(
                force_send=True)
            action_id = self.get_action_id('CancelCommitment')
            message_vals = {'action_id': action_id}

            for contract in self:
                if 'S' in contract.type:
                    # Search pending gifts
                    messages = message_obj.search([
                        ('action_id', '=', self.get_action_id('CreateGift')),
                        ('state', '=', 'new'),
                        ('partner_id', '=', contract.correspondant_id.id),
                        ('child_id', '=', contract.child_id.id)])
                    if contract.child_id.project_id.disburse_gifts and not \
                            contract.cancel_gifts_on_termination:
                        # Send gifts
                        self._change_gift_dates(messages)
                        messages.process_messages()
                    else:
                        # Abort gifts and clean invoices
                        messages.unlink()
                        self.clean_invoices_paid(gifts=True)

                # Only sponsorships are concerned
                if 'S' in contract.type:
                    message_vals.update({
                        'object_id': contract.id,
                    })
                    message_obj.create(message_vals)

        return res

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _on_invoice_line_removal(self, invoice_lines):
        """ Removes the messages linked to the invoice line.
            @param: invoice_lines (dict): {
                line_id: [invoice_id, child_code, product_name, amount]}
        """
        super(recurring_contract, self)._on_invoice_line_removal(
            invoice_lines)
        self._clean_messages(invoice_lines.keys())

    def _clean_messages(self, invoice_line_ids):
        """ Removes the pending messages linked to an invoice line_id
        that was unreconciled. """
        if not isinstance(invoice_line_ids, list):
            invoice_line_ids = [invoice_line_ids]

        # Don't remove CancelCommitment messages
        cancel_id = self.get_action_id('CancelCommitment')
        messages = self.env['gmc.message.pool'].search([
            ('invoice_line_id', 'in', invoice_line_ids),
            ('state', 'in', ['new', 'failure']),
            ('action_id', '!=', cancel_id)])
        messages.unlink()

    def _change_gift_dates(self, messages):
        """ Put gift invoices today if they are in the future. """
        today = datetime.today()
        messages_update = messages.filtered(lambda m: m.invoice_line_id)
        invoices_update = messages.mapped(
            'invoice_line_id.invoice_id').filtered(
            lambda i: datetime.strptime(i.date_invoice, DF) > today)
        invoices_update.write({'date_invoice': today.strftime(DF)})
        messages_update.write({'date': today.strftime(DF + ' %H:%M:%S')})
