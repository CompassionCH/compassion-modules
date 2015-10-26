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
#    @author: Cyril Sester, Emanuel Cino
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
    'name': 'Compassion Sponsorships',
    'version': '1.6',
    'category': 'Other',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['contract_compassion', 'crm',
                'account_cancel', 'partner_compassion',
                'web_m2x_options', 'account_invoice_split_invoice'],
    'data': [
        'view/sponsorship_contract_view.xml',
        'view/sponsorship_contract_group_view.xml',
        'view/end_sponsorship_wizard_view.xml',
        'view/invoice_line_view.xml',
        'view/res_partner_view.xml',
        'view/generate_gift_view.xml',
        'view/account_invoice_split_wizard_view.xml',
        'view/child_view.xml',
        'data/lang.xml',
        'data/sequence.xml',
        'data/sponsorship_product.xml',
        'data/analytic_accounting.xml',
        'workflow/contract_workflow.xml',
    ],
    'demo': [
        'demo/sponsorship_compassion_demo.xml'
    ],
    'installable': True,
    'auto_install': False,
}
