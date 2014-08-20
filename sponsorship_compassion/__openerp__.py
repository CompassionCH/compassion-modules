# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'version': '0.2',
    'category': 'Other',
    'description': """
    """,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['simple_recurring_contract', 'l10n_ch_payment_slip', 
                'l10n_ch', 'account_analytic_plans', 'child_compassion'],
    'data': ['security/sponsorship_groups.xml',
			'view/project_compassion_view.xml',
			'view/contract_view.xml',
            'view/invoice_line_view.xml',
            'view/res_partner_view.xml',
			'data/product.xml',
            'data/payment_terms.xml',
            'data/lang.xml',
            'data/sequence.xml',
            'data/analytic_accounting.xml',
            'data/friday_invoicer_cron.xml',
            'security/ir.model.access.csv',
            'workflow/contract_workflow.xml',
            ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
