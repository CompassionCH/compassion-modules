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
#    @author: Cyril Sester <cyril.sester@outlook.com>
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
    'name': 'LSV Compassion',
    'summary': 'Customize LSV to fit Compassion needs',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'category': 'Other',
    'depends': ['l10n_ch_lsv_dd', 'account_banking_payment'],
    'external_dependencies': {},
    'data': [
    ],
    'demo': [],
    'description': '''
        fr_CH, it_IT, de_DE, en_US and es_ES locales have to be installed on
        your openerp server. You can see which locales are installed by typing
        locale -a.
    ''',
    'active': False,
    'installable': True,
}
