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
#    @author: Emanuel Cino, Serpent Consulting Services Pvt. Ltd.
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
    "name": "Mass Label Reporting",
    "version": "11.0.0.0.0",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "category": "Tools",
    "website": "http://www.serpentcs.com",
    'license': 'AGPL-3',
    'depends': [
        'base',
        'web',
        'report_wkhtmltopdf_param'    # OCA/reporting-engine
    ],
    'data': [
        'views/label_config_view.xml',
        'views/label_print_view.xml',
        'views/label_print_wizard_view.xml',
        'security/ir.model.access.csv',
        'data/label.brand.csv',
        'data/label.config.csv',
        'data/report_paperformat.xml',
        'reports/dynamic_label.xml',
        'reports/one_label.xml'
    ],
    'installable': True,
    'auto_install': False,
}
