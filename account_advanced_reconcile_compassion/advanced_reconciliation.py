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
import datetime

""" We keep track of reconciled debit lines so that we don't
    try to reconcile them with multiple credit lines. """
rec_debit_ids = {}

# We keep track of reconciled credit lines
rec_credit_ids = []


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
            'reconcile_partial_id',
            'move_id',
            'transaction_ref')
        return ["account_move_line.%s" % col for col in aml_cols]

    def _query_debit(self, cr, uid, rec, context=None):
        """ Select all move (debit>0) as candidate.
            Inherit for ordering the debit lines as we want : at first the
            current move_line, then travelling to the past.
            At last, get the future ones.
        """
        # First select the current move_lines
        select_current = "SELECT * FROM (" + self._select(rec)
        from_current = self._from(rec)
        where_current, params_current = self._where(rec)
        where_current += (" AND account_move_line.debit > 0 AND "
                          "account_move_line.date_maturity <= CURRENT_DATE ")
        order_current = " ORDER BY date_maturity DESC ) CURR_MOVE "

        where2_current, params2_current = self._get_filter(
            cr, uid, rec, context=context)

        # Select then the futur debit_moves (to be debited in the future)
        select_future = " UNION ALL " + select_current
        from_future = from_current
        where_future, params_future = self._where(rec)
        where_future += (" AND account_move_line.debit > 0 AND "
                         "account_move_line.date_maturity > CURRENT_DATE) "
                         "FUTURE_MOVE ")
        where2_future, params2_future = where2_current, params2_current

        query = ' '.join((select_current, from_current, where_current,
                          where2_current, order_current, select_future,
                          from_future, where_future, where2_future))

        cr.execute(
            query,
            params_current + params2_current + params_future + params2_future)
        return cr.dictfetchall()

    def _skip_line(self, cr, uid, rec, move_line, context=None):
        """
        When a move_line has no reference or no partner, skip reconciliation.
        Search for open invoices with same reference.
        If the amount of the credit line cannot fully reconcile an integer
        number of invoices, skip the reconciliation.
        """
        if move_line.get('ref') and move_line.get('partner_id'):
            # Search for related customer invoices (same bvr reference).
            invoice_obj = self.pool.get('account.invoice')
            present_invoice_ids = invoice_obj.search(
                cr, uid, [('bvr_reference', '=', move_line['ref']),
                          ('state', '=', 'open'),
                          ('date_due', '<=', datetime.date.today())],
                order='date_due desc', context=context)
            future_invoice_ids = invoice_obj.search(
                cr, uid, [('bvr_reference', '=', move_line['ref']),
                          ('state', '=', 'open'),
                          ('date_due', '>', datetime.date.today())],
                order='date_due asc', context=context)
            invoices = invoice_obj.browse(
                cr, uid, present_invoice_ids + future_invoice_ids,
                context=context)
            total_due = 0.0
            credit_amount = move_line['credit']
            for invoice in invoices:
                total_due += invoice.amount_total
                if total_due == credit_amount:
                    """ The credit line can fully reconcile an integer number of
                        open invoices, it can be reconciled automatically. """
                    return False

            if credit_amount < total_due:
                """ Check for other unreconciled credit lines that could complete
                    the payment and reconcile all invoices. """
                credit_lines = self._query_credit(
                    cr, uid, rec, context=context)
                for other_credit in credit_lines:
                    if other_credit['ref'] == move_line['ref'] and not (
                       other_credit['id'] in rec_credit_ids):
                        credit_amount += other_credit['credit']
                        if total_due == credit_amount:
                            return False

        # Skip reconciliation for this credit line.
        return True

    def _matchers(self, cr, uid, rec, move_line, context=None):
        # We match all move_lines that have the same reference and limit the
        # matches within the "_search_opposites" function
        return (('ref', move_line['ref'].lower().replace(' ', '')),
                )

    def _opposite_matchers(self, cr, uid, rec, move_line, context=None):
        # Must have the same BVR reference
        yield('ref', move_line['transaction_ref'])

    def _search_opposites(self, cr, uid, rec, move_line, opposite_move_lines,
                          context=None):
        """
        Search the opposite debit move lines given a credit move line.
        We limit the search to the number of move_lines that can be
        fully reconciled to avoid partial reconciliation.
        """
        matchers = self._matchers(cr, uid, rec, move_line, context=context)
        opposite_matchers = []
        amount_reconciled = 0.0
        for op in opposite_move_lines:
            if amount_reconciled < move_line['credit']:
                if self._compare_opposite(
                    cr, uid, rec, move_line, op,
                    matchers, context=context) and not self._debit_reconciled(
                        move_line, op):

                    opposite_matchers.append(op)
                    amount_reconciled += op['debit']
            else:
                break

        return opposite_matchers

    def _debit_reconciled(self, credit_line, debit_line):
        """
        Test if a debit line is already fully reconciled.
        If not, update the amount reconciled by credit_line.
        """
        debit_line_id = debit_line['id']
        amount_to_reconcile = min(debit_line['debit'], credit_line['credit'])

        if debit_line_id in rec_debit_ids.keys():
            if rec_debit_ids[debit_line_id] == debit_line['debit']:
                return True
            amount_to_reconcile += rec_debit_ids[debit_line_id]

        rec_debit_ids.update({
            debit_line_id: amount_to_reconcile
        })

        return False
