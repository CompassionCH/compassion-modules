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
#    Copyright (C) 2015-2017 Compassion CH (http://www.compassion.ch)
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
    'name': "Sponsor to beneficiary communication",
    'version': '10.0.1.6.0',
    'category': 'Other',
    'summary': "SBC - Supporter to Beneficiary Communication",
    'sequence': 150,
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': ['sponsorship_compassion', 'web_tree_image'],
    'external_dependencies': {
        'python': ['magic', 'wand', 'numpy', 'pyzbar', 'pdfminer',
                   'matplotlib', 'pyPdf', 'bs4', 'HTMLParser']
        },
    'data': [
        'security/ir.model.access.csv',
        'views/config_view.xml',
        'views/contracts_view.xml',
        'views/partner_compassion_view.xml',
        'views/lang_compassion_view.xml',
        'views/correspondence_view.xml',
        'views/import_letters_history_view.xml',
        'views/correspondence_template_view.xml',
        'views/correspondence_template_page_view.xml',
        'views/correspondence_template_crosscheck_view.xml',
        'views/import_review_view.xml',
        'views/download_letters_view.xml',
        'views/get_letter_image_wizard_view.xml',
        'views/correspondence_s2b_generator_view.xml',
        'views/last_writing_report_view.xml',
        'data/correspondence_template_data.xml',
        'data/correspondence_type.xml',
        'data/child_layouts.xml',
        'data/gmc_action.xml',
        ],
    'demo': ['demo/correspondence_template.xml',
             ],
    'installable': True,
    'auto_install': False,
    }
