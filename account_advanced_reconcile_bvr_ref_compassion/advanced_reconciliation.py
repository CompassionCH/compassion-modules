# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino. Compassion CH
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
import datetime
import pdb

class easy_reconcile_advanced_bvr_ref(orm.TransientModel):

    _name = 'easy.reconcile.advanced.bvr_ref'
    _inherit = 'easy.reconcile.advanced'

    def _base_columns(self, rec):
        """ Mandatory columns for move lines queries
        An extra column aliased as ``key`` should be defined
        in each query."""
        aml_cols = (
            'id',
            'debit',
            'credit',
            'date',
            'period_id',
            'ref',
            'name',
            'partner_id',
            'account_id',
            'move_id',
            'transaction_ref')
        return ["account_move_line.%s" % col for col in aml_cols]    
    
    def _query_debit(self, cr, uid, rec, context=None):
        """ Select all move (debit>0) as candidate.
            Inherit for ordering the debit lines as we want : at first the current move_line, then travelling to the past.
            At last, get the future ones.
        """
        # First select the current move_lines
        select_current = "SELECT * FROM (" + self._select(rec)
        from_current = self._from(rec)
        where_current, params_current = self._where(rec)
        where_current += " AND account_move_line.debit > 0 AND account_move_line.date_maturity <= CURRENT_DATE "
        order_current = " ORDER BY date_maturity DESC ) CURR_MOVE "

        where2_current, params2_current = self._get_filter(cr, uid, rec, context=context)
        
        # Select then the futur debit_moves (to be debited in the future)
        select_future = " UNION ALL " + select_current
        from_future = from_current
        where_future, params_future = self._where(rec)
        where_future += " AND account_move_line.debit > 0 AND account_move_line.date_maturity > CURRENT_DATE) FUTURE_MOVE "
        where2_future, params2_future = where2_current, params2_current

        query = ' '.join((select_current, from_current, where_current, where2_current, order_current, select_future, from_future, where_future, where2_future))

        cr.execute(query, params_current + params2_current + params_future + params2_future)
        return cr.dictfetchall()
    
    def _skip_line(self, cr, uid, rec, move_line, context=None):
        """
        When the move_line has no reference or no partner, skip the credit line.
        Search for open invoices with same reference. If the amount of the credit line is not a multiple of the amount of one invoice, skip the credit line.
        If it can match, set the number of move lines that can be reconciled with the amount of the credit.
        """
        if move_line.get('ref') and move_line.get('partner_id'):
            # Search for related customer invoices (same bvr reference).
            invoice_obj = self.pool.get('account.invoice')
            present_invoice_ids = invoice_obj.search(cr, uid, [('bvr_reference','=',move_line['ref']),('state','=','open'),('date_due','<=', datetime.date.today())], order='date_due desc', context=context)
            future_invoice_ids = invoice_obj.search(cr, uid, [('bvr_reference','=',move_line['ref']),('state','=','open'),('date_due','>', datetime.date.today())], order='date_due asc', context=context)
            invoices = invoice_obj.browse(cr, uid, present_invoice_ids + future_invoice_ids, context=context)
            total_due = 0.0
            for invoice in invoices:
                total_due += invoice.amount_total
                if total_due == move_line['credit']:
                    # The credit line can fully reconcile an integer number of open invoices, it can be reconciled automatically.
                    return False
                    
        # Skip reconciliation for this credit line.
        return True

    def _matchers(self, cr, uid, rec, move_line, context=None):
        # We match all move_lines that have the same reference and limit the matches within the "_search_opposites" function
        return (('ref', move_line['ref'].lower().replace(' ', '')),
                )
  
    def _opposite_matchers(self, cr, uid, rec, move_line, context=None):
        # Must have the same BVR reference
        yield('ref', move_line['transaction_ref'])

    def _search_opposites(self, cr, uid, rec, move_line, opposite_move_lines, context=None):
        """
        Search the opposite move lines for a move line

        We limit the search to the number of move_lines that can be fully reconciled to avoid partial reconciliation.
        """
        matchers = self._matchers(cr, uid, rec, move_line, context=context)
        opposite_matchers = []
        amount_reconciled = 0.0
        for op in opposite_move_lines:
            if amount_reconciled < move_line['credit']:
                if self._compare_opposite(cr, uid, rec, move_line, op, matchers, context=context):
                    opposite_matchers.append(op)
                    amount_reconciled += op['debit']
            else:
                break
        return opposite_matchers