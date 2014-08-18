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
    'name': 'Install all modules needed for Compassion CH',
    'version': '1.0.0',
    'category': 'Other',
    'description': """
        This module does nothing but install a bunch of useful modules developped for Compassion CH.
        
        Warning : This module requires python-MySQLdb to be installed on the server.
    """,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['disable_openerp_online',
                'account_statement_bvr_ref_completion',
                'account_statement_ext_compassion',
                'account_advanced_reconcile_bvr_ref_compassion',
                'lsv_compassion',
                'bvr_ref_compassion',
                'crm_child_sponsorship',
                'partner_compassion',
                'mail_thread_compassion',
                'password_pusher_compassion',
                'l10n_ch_account_statement_base_import',
                ],
    'data': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
