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
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    @author: David Coninckx
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
    'name': 'Compassion Contracts',
    'version': '1.2',
    'category': 'Other',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['recurring_contract', 'account_banking_mandate',
                'child_compassion', 'account_analytic_compassion',
                'l10n_ch_payment_slip'],
    'data': [
        'view/end_contract_wizard_view.xml',
        'view/contract_group_view.xml',
        'view/contract_origin_view.xml',
        'view/contract_view.xml',
        'view/activate_contract_view.xml',
        'workflow/contract_workflow.xml',
        'workflow/invoice_workflow.xml',
        'security/ir.model.access.csv',
        'data/friday_invoicer_cron.xml',
        'data/product.xml',
        'data/payment_terms.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
