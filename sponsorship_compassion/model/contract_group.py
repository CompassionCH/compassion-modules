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

import time

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools import mod10r


class contract_group(orm.Model):
    ''' Add BVR on groups and add BVR ref and analytics_id in invoices '''
    _inherit = 'recurring.contract.group'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for gr in self.browse(cr, uid, ids, context):
            name = ''
            if gr.payment_term_id:
                name = gr.payment_term_id.name
            if gr.bvr_reference:
                name += ' ' + gr.bvr_reference
            if name == '':
                name = gr.partner_id.name + ' ' + str(gr.id)
            res.append((gr.id, name))
        return res

    def _get_op_payment_term(self, cr, uid, context=None):
        ''' Get Permanent Order Payment Term, to set it by default. '''
        payment_term_id = self.pool.get('account.payment.term').search(
            cr, uid, [('name', '=', 'Permanent Order')], context=context)
        return payment_term_id[0]

    _columns = {
        'bvr_reference': fields.char(size=32, string=_('BVR Ref'),
                                     track_visibility="onchange"),
        'advance_billing': fields.selection([
            ('monthly', _('Monthly')),
            ('bimonthly', _('Bimonthly')),
            ('quarterly', _('Quarterly')),
            ('fourmonthly', _('Four-monthly')),
            ('biannual', _('Bi-annual')),
            ('annual', _('Annual'))], _('Frequency'),
            help=_('Advance billing allows you to generate invoices in '
                   'advance. For example, you can generate the invoices '
                   'for each month of the year and send them to the '
                   'customer in january.'), track_visibility="onchange"),
        'payment_term_id': fields.many2one(
            'account.payment.term', _('Payment Term'),
            domain=['|', '|', '|', ('name', 'ilike', 'BVR'),
                    ('name', 'ilike', 'LSV'),
                    ('name', 'ilike', 'Postfinance'),
                    ('name', 'ilike', 'Permanent')],
            track_visibility="onchange"),
    }

    _defaults = {
        'payment_term_id': _get_op_payment_term,
        'advance_billing': 'monthly',
    }

    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        res = {}
        if not partner_id:
            return {'value': {'bvr_reference': ''}}
        partner = self.pool.get('res.partner').browse(cr, uid, partner_id,
                                                      context=context)
        if partner.ref:
            computed_ref = self._compute_partner_ref(cr, uid, partner,
                                                     context)
            if computed_ref:
                res['value'] = {'bvr_reference': computed_ref}
            else:
                res['warning'] = {'title': _('Warning'),
                                  'message': _('The reference of the partner '
                                               'has not been set, or is in '
                                               'wrong format. Please make sure'
                                               ' to enter a valid BVR '
                                               'reference for the contract.')}
        return res

    def on_change_payment_term(self, cr, uid, ids, payment_term_id,
                               partner_id, context=None):
        ''' Generate new bvr_reference if payment term is Permanent Order
        or BVR '''
        res = {'value': {'bvr_reference': ''}}
        need_bvr_ref_term_ids = self.pool.get('account.payment.term').search(
            cr, uid, [('name', 'in', ('Permanent Order', 'BVR'))],
            context=context)
        if payment_term_id in need_bvr_ref_term_ids:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id,
                                                          context=context)
            if partner.ref:
                res['value'].update({
                    'bvr_reference': self._compute_partner_ref(
                        cr, uid, partner, context)})

        return res

    def on_change_bvr_ref(self, cr, uid, ids, bvr_reference,
                          context=None):
        ''' Test the validity of a reference number. '''
        is_valid = bvr_reference and bvr_reference.isdigit()
        if is_valid and len(bvr_reference) == 26:
            bvr_reference = mod10r(bvr_reference)
        elif is_valid and len(bvr_reference) == 27:
            valid_ref = mod10r(bvr_reference[:-1])
            is_valid = (valid_ref == bvr_reference)
        else:
            is_valid = False

        res = {}
        if is_valid:
            res['value'] = {'bvr_reference': bvr_reference}
        elif bvr_reference:
            res['warning'] = {'title': _('Warning'),
                              'message': _('The reference of the partner '
                                           'has not been set, or is in '
                                           'wrong format. Please make sure'
                                           ' to enter a valid BVR '
                                           'reference for the contract.')}
        return res

    def _compute_partner_ref(self, cr, uid, partner, context=None):
        """ Generates a new BVR Reference.
        See file \\nas\it\devel\Code_ref_BVR.xls for more information."""
        result = '0' * (9 + (7 - len(partner.ref))) + partner.ref
        count_groups = str(self.search(
            cr, uid, [('partner_id', '=', partner.id)], context=context,
            count=True))
        result += '0' * (5 - len(count_groups)) + count_groups
        # Type '0' = Sponsorship
        result += '0'
        result += '0' * 4

        if len(result) == 26:
            return mod10r(result)

    def _setup_inv_data(self, cr, uid, con_gr, journal_ids, invoicer_id,
                        context=None):
        ''' Inherit to add BVR ref '''
        inv_data = super(contract_group, self)._setup_inv_data(cr, uid, con_gr,
                                                               journal_ids,
                                                               invoicer_id,
                                                               context)

        ref = ''
        if con_gr.bvr_reference:
            ref = con_gr.bvr_reference
        elif (con_gr.payment_term_id
              and (_('LSV') in con_gr.payment_term_id.name
                   or _('Direct Debit') in con_gr.payment_term_id.name)):
            seq = self.pool['ir.sequence']
            ref = mod10r(seq.next_by_code(cr, uid, 'contract.bvr.ref'))
        inv_data.update({
            'bvr_reference': ref})

        return inv_data

    def _setup_inv_line_data(self, cr, uid, contract_line, invoice_id,
                             context=None):
        ''' Inherit to add analytic distribution '''
        inv_line_data = super(contract_group, self)._setup_inv_line_data(
            cr, uid, contract_line, invoice_id, context)

        product_id = contract_line.product_id.id
        partner_id = contract_line.contract_id.partner_id.id
        analytic = self.pool.get('account.analytic.default').account_get(
            cr, uid, product_id, partner_id, uid, time.strftime('%Y-%m-%d'),
            context=context)
        if analytic and analytic.analytics_id:
            inv_line_data.update({'analytics_id': analytic.analytics_id.id})

        return inv_line_data

    def _get_gen_states(self):
        return ['waiting', 'active']
