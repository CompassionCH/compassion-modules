# -*- encoding: utf-8 -*-
##############################################################################
#
#    Compassion asset customizing module for openERP
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    @author: Cyril Sester <csester@compassion.ch>
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
    'name': 'Assets Compassion',
    'summary': 'Modifications to fit Compassion needs',
    'version': '1.0',
    'license': 'AGPL-3',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'category': 'Accounting & Finance',
    'depends': ['account_analytic_plans','account_asset_management'],
    'external_dependencies': {},
    'data': ['account_asset_view.xml'],
    'demo': [],
    'description': '''
        Replace the account by the analytic account.
        ! - This module overrides the prorata temporis asset process.
    ''',
    'active': False,
    'installable': True,
}
