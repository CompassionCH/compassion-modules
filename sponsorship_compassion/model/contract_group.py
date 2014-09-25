# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
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

    _columns = {
        'bvr_reference': fields.char(size=32, string=_('BVR Ref')),
    }

    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        res = {}
        if not partner_id:
            return {'value': {'bvr_reference': ''}}
        partner = self.pool.get('res.partner').browse(cr, uid, partner_id,
                                                      context=context)
        if partner.ref:
            computed_ref = self._compute_partner_ref(partner.ref)
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

    def _compute_partner_ref(self, reference):
        # TODO : Retrieve existing ref if there is already a contract !
        result = '0' * (9 + (7 - len(reference))) + reference
        # TODO : Now, only one reference per partner. We should create another
        # number if type of payment is not the same as an existing contract
        # for that partner.
        result += ('0' * 4) + '1'
        # TODO : Other types than sponsorship !
        # Type '0' = Sponsorship
        result += '0'
        # TODO : ID child, bordereau or Fonds
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
