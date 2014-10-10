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

from openerp.osv import orm


class account_invoice(orm.Model):
    """ Adds two buttons for opening transactions of partner from invoice
    which eases the verification of generated invoices for the user."""

    _inherit = "account.invoice"

    def show_transactions(self, cr, uid, ids, context=None):
        partner_obj = self.pool.get('res.partner')
        partner_ids = [self.browse(cr, uid, ids[0], context).partner_id.id]
        return partner_obj.show_lines(cr, uid, partner_ids, context)

    def show_move_lines(self, cr, uid, ids, context=None):
        partner_id = self.browse(cr, uid, ids[0], context).partner_id.id
        action = {
            'name': 'Journal Items',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'account.move.line',
            'src_model': 'account.invoice',
            'context': {'search_default_partner_id': [partner_id],
                        'default_partner_id': partner_id,
                        'search_default_unreconciled': 1},
        }

        return action
