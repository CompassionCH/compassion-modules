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
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
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
    'name': "Sponsor to beneficiary communication",
    'version': '0.1',
    'category': 'Other',
    'summary': "SBC - Sponsor to beneficiary communication",
    'sequence': 150,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['sponsorship_compassion', 'web_tree_image'],
    'external_dependencies': {
        'java': ['zxing'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/country_compassion_view.xml',
        'views/partner_compassion_view.xml',
        'views/lang_compassion_view.xml',
        'views/sponsorship_correspondence_view.xml',
        'views/import_letters_history_view.xml',
        'views/import_letter_line_view.xml',
        'data/lang_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
