# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino. Copyright Compassion CH
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

{'name': 'Advanced Reconcile Transaction Ref',
 'description':  """
Advanced reconciliation method for the module account_advanced_reconcile
========================================================================
Reconcile rules with bvr_ref of invoice.

It finds a matching invoice for the move_line and reconciles only if the amount of the payment corresponds or if it is a multiple
of the invoice amount. If many invoices are found, the first reconciled invoice is the current invoice (last invoice that is not in future).
Then it reconciles the other invoices from last invoice to first.

""",
 'version': '1.0',
 'author': 'Compassion CH',
 'category': 'Finance',
 'website': 'http://www.compassion.ch',
 'depends': ['account_advanced_reconcile','l10n_ch_payment_slip_base_transaction_id'],
 'data': ['easy_reconcile_view.xml'],
 'demo': [],
 'test': [],
 'auto_install': False,
 'installable': True,
 'images': []
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
