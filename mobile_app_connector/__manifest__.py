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
#    Copyright (C) 2018-2019 Compassion CH (http://www.compassion.ch)
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
    'name': 'Compassion EU Mobile App Connector',
    'version': '11.0.1.0.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'https://github.com/CompassionCH/compassion-modules/tree/10.0',
    'depends': [
        'sbc_compassion',
        'partner_contact_birthdate',
        'base_geolocalize',
        'firebase_connector',           # compassion-modules
        'sms_sponsorship',              # compassion-modules
        'thankyou_letters',        # compassion-modules
        'crm_claim',                    # oca_addons/crm
        'wordpress_configuration'       # compassion-modules
    ],
    'external_dependencies': {
        'python': ['simplejson', 'bs4', 'requests', 'detectlanguage'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/access_rules.xml',
        'data/tile_type_data.xml',
        'data/default_hub.xml',
        'data/default_banner.xml',
        'data/prayer_tile.xml',
        'data/template_mail_user_not_found.xml',
        'data/ir_cron.xml',
        'data/request_sequence.xml',
        'data/crm_claim_category_data.xml',
        'views/wp_post_view.xml',
        'views/wp_post_category_view.xml',
        'views/app_banner_view.xml',
        'views/app_settings_view.xml',
        'views/app_writing_view.xml',
        'views/tile_type_view.xml',
        'views/tile_view.xml',
        'views/product_view.xml',
        'views/app_feedback_view.xml',
        'views/firebase_registration.xml',
        'templates/registration_form.xml',
        'views/firebase_notification.xml',
        'views/communication_job.xml',
        'views/communication_config.xml',
        'views/res_partner.xml'
    ],
    'demo': [
    ],
    'development_status': 'Beta',
    'installable': True,
    'auto_install': False,
    'post_init_hook': "load_mappings"
}
