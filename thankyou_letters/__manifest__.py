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
#    Copyright (C) 2016-2020 Compassion CH (http://www.compassion.ch)
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
    'name': 'Thank You Letters',
    'version': '10.0.2.1.1',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': [
        'partner_communication',
        'advanced_translation',
        'web_widget_digitized_signature',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/donation_report.xml',
        'data/email_template.xml',
        'data/communication_config.xml',
        'data/ir_cron.xml',
        'views/success_story_view.xml',
        'views/communication_job_view.xml',
        'views/account_invoice_view.xml',
        'views/product_view.xml',
        'views/res_partner_view.xml',
        'views/thankyou_config_view.xml',
        'views/generate_communication_wizard_view.xml',
    ],
    'demo': [
        'demo/demo_data.xml'
    ],
    'installable': True,
    'auto_install': False,
}
