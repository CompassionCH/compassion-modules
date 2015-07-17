# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api, exceptions, netsvc, _
from openerp.tools import mod10r


class contract_group(models.Model):
    """ Add BVR on groups and add BVR ref and analytic_id
    in invoices """
    _inherit = 'recurring.contract.group'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    bvr_reference = fields.Char(
        'BVR Ref', size=32, track_visibility="onchange")
    payment_term_id = fields.Many2one(
        'account.payment.term', 'Payment Term',
        domain=['|', '|', '|', ('name', 'ilike', 'BVR'),
                ('name', 'ilike', 'LSV'),
                ('name', 'ilike', 'Postfinance'),
                ('name', 'ilike', 'Permanent')], track_visibility='onchange',
        default=lambda self: self._get_op_payment_term())
    change_method = fields.Selection(default='clean_invoices')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _get_op_payment_term(self):
        """ Get Permanent Order Payment Term, to set it by default. """
        record = self.env.ref(
            'contract_compassion.payment_term_permanent_order')
        return record.id

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    @api.depends('payment_term_id', 'bvr_reference', 'partner_id')
    def name_get(self):
        res = list()
        for gr in self:
            name = ''
            if gr.payment_term_id:
                name = gr.payment_term_id.name
            if gr.bvr_reference:
                name += ' ' + gr.bvr_reference
            if name == '':
                name = gr.partner_id.name + ' ' + str(gr.id)
            res.append((gr.id, name))
        return res

    @api.multi
    def write(self, vals):
        """ If sponsor changes his payment term to LSV or DD,
        change the state of related contracts so that we wait
        for a valid mandate before generating new invoices.
        """
        contract_ids = list()
        inv_vals = dict()
        uid = self.env.user.id
        if 'payment_term_id' in vals:
            inv_vals['payment_term'] = vals['payment_term_id']
            payment_term = self.env['account.payment.term'].with_context(
                lang='en_US').browse(vals['payment_term_id'])
            payment_name = payment_term.name
            wf_service = netsvc.LocalService('workflow')
            for group in self:
                old_term = group.payment_term_id.name
                for contract_id in group.contract_ids.ids:
                    contract_ids.append(contract_id)
                    if 'LSV' in payment_name or 'Postfinance' in payment_name:
                        wf_service.trg_validate(
                            uid, 'recurring.contract', contract_id,
                            'will_pay_by_lsv_dd', self.env.cr)
                        # LSV/DD Contracts need no reference
                        if group.bvr_reference and \
                                'multi-months' not in payment_name:
                            vals['bvr_reference'] = False
                    elif 'LSV' in old_term or 'Postfinance' in old_term:
                        wf_service.trg_validate(
                            uid, 'recurring.contract', contract_id,
                            'mandate_validated', self.env.cr)
        if 'bvr_reference' in vals:
            inv_vals['bvr_reference'] = vals['bvr_reference']
            contract_ids.extend(self.mapped('contract_ids.id'))

        res = super(contract_group, self).write(vals)

        if contract_ids:
            # Update related open invoices to reflect the changes
            inv_line_obj = self.env['account.invoice.line']
            inv_lines = inv_line_obj.search([
                ('contract_id', 'in', contract_ids),
                ('state', 'not in', ('paid', 'cancel'))])
            invoices = inv_lines.mapped('invoice_id')
            invoices.action_cancel()
            invoices.action_cancel_draft()
            invoices.write(inv_vals)
            wf_service = netsvc.LocalService('workflow')
            for invoice in invoices:
                wf_service.trg_validate(
                    self.env.user.id, 'account.invoice', invoice.id,
                    'invoice_open', self.env.cr)
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def compute_partner_bvr_ref(self, partner=None, is_lsv=False):
        """ Generates a new BVR Reference.
        See file \\nas\it\devel\Code_ref_BVR.xls for more information."""
        self.ensure_one()
        if self.exists():
            # If group was already existing, retrieve any existing reference
            ref = self.bvr_reference
            if ref:
                return ref
        partner = partner or self.partner_id
        result = '0' * (9 + (7 - len(partner.ref))) + partner.ref
        count_groups = str(self.search_count(
            [('partner_id', '=', partner.id)]))
        result += '0' * (5 - len(count_groups)) + count_groups
        # Type '0' = Sponsorship
        result += '0'
        result += '0' * 4

        if is_lsv:
            result = '004874969' + result[9:]
        if len(result) == 26:
            return mod10r(result)

    def clean_invoices(self):
        """ Override clean_invoices to delete cancelled invoices """
        inv_ids = super(contract_group, self).clean_invoices()
        if inv_ids:
            inv_ids = list(inv_ids)
            self.env.cr.execute(
                "DELETE FROM account_invoice "
                "WHERE id IN ({0})".format(
                    ','.join([str(id) for id in inv_ids])))
        return inv_ids

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('partner_id')
    def on_change_partner_id(self):
        if not self.partner_id:
            self.bvr_reference = False
            return

        partner = self.partner_id
        if partner.ref:
            computed_ref = self.compute_partner_bvr_ref(partner)
            if computed_ref:
                self.bvr_reference = computed_ref
            else:
                raise exceptions.Warning(
                    _('Warning'),
                    _('The reference of the partner has not been set, '
                      'or is in wrong format. Please make sure to enter a '
                      'valid BVR reference for the contract.'))

    @api.onchange('payment_term_id')
    def on_change_payment_term(self):
        """ Generate new bvr_reference if payment term is Permanent Order
        or BVR """
        payment_term_id = self.payment_term_id and self.payment_term_id.id
        payment_term_obj = self.env['account.payment.term'].with_context(
            lang='en_US')
        need_bvr_ref_term_ids = payment_term_obj.search([
            '|', ('name', 'in', ('Permanent Order', 'BVR')),
            ('name', 'like', 'multi-months')]).ids
        lsv_term_ids = payment_term_obj.search(
            [('name', 'like', 'LSV')]).ids
        if payment_term_id in need_bvr_ref_term_ids:
            is_lsv = payment_term_id in lsv_term_ids
            partner = self.partner_id
            if partner.ref and (not self.bvr_reference or is_lsv):
                self.bvr_reference = self.compute_partner_bvr_ref(
                    partner, is_lsv)
        else:
            self.bvr_reference = False

    @api.onchange('bvr_reference')
    def on_change_bvr_ref(self):
        """ Test the validity of a reference number. """
        bvr_reference = self.bvr_reference
        is_valid = bvr_reference and bvr_reference.isdigit()
        if is_valid and len(bvr_reference) == 26:
            bvr_reference = mod10r(bvr_reference)
        elif is_valid and len(bvr_reference) == 27:
            valid_ref = mod10r(bvr_reference[:-1])
            is_valid = (valid_ref == bvr_reference)
        else:
            is_valid = False

        if is_valid:
            self.bvr_reference = bvr_reference
        elif bvr_reference:
            raise exceptions.Warning(
                _('Warning'),
                _('The reference of the partner has not been set, or is in '
                  'wrong format. Please make sure to enter a valid BVR '
                  'reference for the contract.'))

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _setup_inv_data(self, journal_ids, invoicer):
        """ Inherit to add BVR ref """
        self.ensure_one()
        inv_data = super(contract_group, self)._setup_inv_data(
            journal_ids, invoicer)

        ref = ''
        if self.bvr_reference:
            ref = self.bvr_reference
        elif (self.payment_term_id and
              (_('LSV') in self.payment_term_id.name or
               _('Direct Debit') in self.payment_term_id.name)):
            seq = self.pool['ir.sequence']
            ref = mod10r(seq.next_by_code('contract.bvr.ref'))
        inv_data.update({
            'bvr_reference': ref})

        return inv_data

    def _get_gen_states(self):
        return ['waiting', 'active']
