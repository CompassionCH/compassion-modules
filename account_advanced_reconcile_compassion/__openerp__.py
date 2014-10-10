# -*- encoding: utf-8 -*-
##############################################################################
#
#       ______ Releasing children from poverty      _
#      / ____/___  ____ ___  ____  ____ ___________(_)___  ____
#     / /   / __ \/ __ `__ \/ __ \/ __ `/ ___/ ___/ / __ \/ __ \
#    / /___/ /_/ / / / / / / /_/ / /_/ (__  |__  ) / /_/ / / / /
#    \____/\____/_/ /_/ /_/ .___/\__,_/____/____/_/\____/_/ /_/
#                        /_/
#                            in Jesus' name
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
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

{
    'name': 'Advanced Reconcile Compassion',
    'description':  """
    Reconcile rules with bvr_ref of invoice for Compassion CH.

    It finds a matching invoice for the move_line and reconciles only if the
    amount of the payment corresponds or if it is a multiple of the invoice
    amount. If many invoices are found, the first reconciled invoice is the
    current invoice (last invoice that is not in future).
    Then it reconciles the other invoices from last invoice to first.
    """,
    'version': '1.0',
    'author': 'Compassion CH',
    'category': 'Finance',
    'website': 'http://www.compassion.ch',
    'depends': ['account_advanced_reconcile',
                'l10n_ch_payment_slip_base_transaction_id',
                'account_analytic_default',
                'sponsorship_compassion',
                'account_cancel'],
    'data': ['view/easy_reconcile_view.xml',
             'view/reconcile_fund_wizard_view.xml',
             'view/reconcile_split_payment_wizard_view.xml'],
    'js': ['static/src/js/account_move_reconciliation.js'],
    'qweb': ['static/src/xml/account_move_reconciliation.xml'],
    'demo': [],
    'test': [],
    'auto_install': False,
    'installable': True,
    'images': []
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
