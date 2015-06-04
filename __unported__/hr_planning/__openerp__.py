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
#    @author: David Coninckx <david@coninckx.com>
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
    'name': 'Compassion CH - Planning',
    'version': '1.1',
    'category': 'CRM',
    'sequence': 150,
    'description': """Compassion CRM - Human Resources Planning
==============================================================================

This module helps Compassion CH to manage the schedule of HR.

 * Add a calendar view for HR contract
 * Create a calendar view to compare HR contract with HR holidays
""",
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['hr_contract', 'hr_holidays'],
    'data': [
        'view/hr_planning_view.xml',
        'view/hr_planning_wizard_view.xml',
        'view/hr_planning_move_request_view.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
    'css': ['static/src/css/hr_planning.css'],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
