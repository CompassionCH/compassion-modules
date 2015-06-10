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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class res_partner(orm.Model):
    _inherit = 'res.partner'

    def _get_related_contracts(self, cr, uid, ids, field_names, arg, context):
        """ Returns the contracts of the sponsor of given type
        ('fully_managed', 'correspondant' or 'payer')
        """
        res = dict()
        field_res = dict()
        contract_obj = self.pool.get('recurring.contract')
        for id in ids:
            correspondant_ids = contract_obj.search(
                cr, uid, [('correspondant_id', '=', id),
                          ('type', '=', 'S'),
                          ('fully_managed', '=', False)],
                order='start_date desc', context={})
            paid_ids = contract_obj.search(
                cr, uid, [('partner_id', '=', id),
                          ('type', '=', 'S'),
                          ('fully_managed', '=', False)],
                order='start_date desc', context={})
            fully_managed_ids = contract_obj.search(
                cr, uid, [('partner_id', '=', id),
                          ('type', '=', 'S'),
                          ('fully_managed', '=', True)],
                order='start_date desc', context={})

            field_res['contracts_fully_managed'] = fully_managed_ids
            field_res['contracts_paid'] = paid_ids
            field_res['contracts_correspondant'] = correspondant_ids
            res[id] = field_res.copy()

        return res

    def _write_related_contracts(self, cr, uid, id, name, value, inv_arg,
                                 context=None):
        value_obj = self.pool.get('recurring.contract')
        for line in value:
            if line[0] == 1:  # one2many update
                value_id = line[1]
                value_obj.write(cr, uid, [value_id], line[2])
        return True

    _columns = {
        'contracts_fully_managed': fields.function(
            _get_related_contracts, type="one2many",
            obj="recurring.contract",
            fnct_inv=_write_related_contracts, multi='sponsorships',
            string='Fully managed sponsorships',
            order="state asc",),
        'contracts_paid': fields.function(
            _get_related_contracts, type="one2many",
            obj="recurring.contract",
            fnct_inv=_write_related_contracts, multi='sponsorships',
            string='Sponsorships as payer only'),
        'contracts_correspondant': fields.function(
            _get_related_contracts, type="one2many",
            obj="recurring.contract",
            fnct_inv=_write_related_contracts, multi='sponsorships',
            string='Sponsorships as correspondant only'),
    }

    def show_lines(self, cr, uid, ids, context=None):
        try:
            ir_model_data = self.pool.get('ir.model.data')
            view_id = ir_model_data.get_object_reference(
                cr, uid, 'sponsorship_compassion',
                'view_invoice_line_partner_tree')[1]
        except ValueError:
            view_id = False
        context['search_default_partner_id'] = ids
        action = {
            'name': _('Related invoice lines'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'account.invoice.line',
            'view_id': view_id,
            'views': [(view_id, 'tree'), (False, 'form')],
            'target': 'current',
            'context': context,
        }

        return action

    def show_move_lines(self, cr, uid, ids, context=None):
        try:
            ir_model_data = self.pool.get('ir.model.data')
            move_line_id = ir_model_data.get_object_reference(
                cr, uid, 'account',
                'view_move_line_tree')[1]
        except ValueError:
            move_line_id = False
        context['search_default_partner_id'] = ids
        action = {
            'name': _('Related invoice lines'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'account.move.line',
            'view_id': move_line_id,
            'views': [(move_line_id, 'tree')],
            'target': 'current',
            'context': context,
        }

        return action

    def create_contract(self, cr, uid, ids, context=None):
        context.update({
            'default_partner_id': ids[0],
            'default_type': 'S',
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Sponsorship'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'recurring.contract',
            'target': 'current',
            'context': context
        }

    def unreconciled_transaction_items(self, cr, uid, ids, context=None):
        context['search_default_unreconciled'] = 1
        return self.show_move_lines(cr, uid, ids, context)

    def receivable_transaction_items(self, cr, uid, ids, context=None):
        account_ids = self.pool.get('account.account').search(
            cr, uid,
            [('code', '=', '1050')],
            context=context)
        context['search_default_account_id'] = account_ids[0]
        return self.show_move_lines(cr, uid, ids, context)
