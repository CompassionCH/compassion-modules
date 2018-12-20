# -*- coding: utf-8 -*-
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
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
#    @author: David Coninckx, Emanuel Cino
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

# pylint: disable=C8101
{
    'name': 'Compassion Contracts',
    'version': '10.0.2.2.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': ['recurring_contract', 'child_compassion', 'utm'],
    'data': [
        'views/end_contract_wizard_view.xml',
        'views/contract_group_view.xml',
        'views/contract_origin_view.xml',
        'views/contract_view.xml',
        'views/activate_contract_view.xml',
        'views/utm_medium_view.xml',
        'workflow/contract_workflow.xml',
        'security/ir.model.access.csv',
        'data/friday_invoicer_cron.xml',
        'data/product.xml',
        'data/utm_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
