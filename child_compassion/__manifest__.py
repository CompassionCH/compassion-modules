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
#    Copyright (C) 2014-2019 Compassion CH (http://www.compassion.ch)
#    @author: Cyril Sester, Emanuel Cino
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
    'name': 'Compassion Children',
    'version': '12.0.1.0.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'development_status': 'Stable',
    'depends': [
        'mail_tracking',         # social/mail_tracking
        'message_center_compassion',
        'advanced_translation'
    ],
    'external_dependencies': {
        'python': [
            'pyquery',
            'pytz',
            'timezonefinder',
        ]
    },
    'data': [
        'security/sponsorship_groups.xml',
        'security/ir.model.access.csv',
        'views/child_compassion_view.xml',
        'views/field_office_view.xml',
        'views/field_office_learning_view.xml',
        'views/child_holds_view.xml',
        'views/global_childpool_view.xml',
        'views/project_compassion_view.xml',
        'views/gmc_message_view.xml',
        'views/compassion_reservation_view.xml',
        'views/field_office_disaster_alert_view.xml',
        'views/res_config_view.xml',
        'views/notification_settings_view.xml',
        'views/child_pictures_view.xml',
        'views/demand_planning.xml',
        'views/res_lang_compassion_view.xml',
        'data/validity_checks_cron.xml',
        'data/child.hobby.csv',
        'data/child.household.duty.csv',
        'data/child.project.activity.csv',
        'data/child.school.subject.csv',
        'data/child.christian.activity.csv',
        'data/child.chronic.illness.csv',
        'data/child.physical.disability.csv',
        'data/child.future.hope.csv',
        'data/connect.month.csv',
        'data/compassion_mapping.xml',
        'data/gmc_action.xml',
        'data/compassion.field.office.csv',
        'data/field.office.learning.csv',
        'data/global_partner.xml',
        'data/res.lang.compassion.csv',
        'data/fcp.involvement.csv',
        'data/fcp.church.ministry.csv',
        'data/fcp.program.csv',
        'data/demand_planning_cron.xml',
        'data/fcp.church.facility.csv',
        'data/fcp.church.utility.csv',
        'data/fcp.cognitive.activity.csv',
        'data/fcp.community.occupation.csv',
        'data/fcp.diet.csv',
        'data/fcp.lifecycle.reason.csv',
        'data/fcp.suspension.extension.reason.csv',
        'data/fcp.mobile.device.csv',
        'data/fcp.physical.activity.csv',
        'data/fcp.school.cost.csv',
        'data/fcp.sociological.activity.csv',
        'data/fcp.spiritual.activity.csv',
        'data/fo.high.risk.csv',
        'data/fo.disaster.loss.csv',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'post_init_hook': "load_mappings"
}
