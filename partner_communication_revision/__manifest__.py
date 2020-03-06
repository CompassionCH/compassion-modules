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
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
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

# pylint: disable=C8101
{
    'name': 'Partner Communication Revisions',
    'version': '12.0.1.0.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': [
        'partner_communication',
        'web_tree_dynamic_colored_field'  # OCA/web
    ],
    'external_dependencies': {
        'python': ['pyquery', 'regex', 'bs4', 'PyPDF2']
    },
    'data': [
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'data/communication_config.xml',
        'data/reminder_cron.xml',
        'views/new_proposition_wizard_view.xml',
        'views/validate_revision_wizard_view.xml',
        'views/communication_config_view.xml',
        'views/revision_preview_view.xml',
        'views/communication_revision_view.xml',
        'views/communication_keyword_view.xml',
        'views/cancel_revision_wizard_view.xml',
        'views/submit_revision_wizard_view.xml',
        'data/install.xml'
    ],
    'qweb': [],
    'demo': [
        'data/demo.xml'
    ],
    'installable': True,
    'auto_install': False
}
