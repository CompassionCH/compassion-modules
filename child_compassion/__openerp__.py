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
    'name': 'Compassion Children',
    'version': '1.4.1',
    'category': 'Other',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['mail', 'web_m2x_options', 'document'],
    'external_dependencies': {
        'python': ['urllib3', 'certifi'],
    },
    'data': [
        'security/sponsorship_groups.xml',
        'security/ir.model.access.csv',
        'view/child_depart_wizard_view.xml',
        'view/child_compassion_view.xml',
        'view/child_compassion_property_view.xml',
        'view/child_description_wizard_view.xml',
        'view/project_compassion_view.xml',
        'view/translated_values_view.xml',
        'view/country_compassion_view.xml',
        'view/delegate_child_wizard.xml',
        'view/undelegate_child_wizard.xml',
        'view/project_description_wizard_view.xml',
        'view/project_compassion_age_groups_view.xml',
        'workflow/child_workflow.xml',
        'data/delegate_child_compassion_cron.xml',
        'data/child_compassion_template.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
