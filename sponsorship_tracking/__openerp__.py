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
#    @author: David Coninckx
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
    'name': 'Compassion Sponsorships Tracking',
    'version': '1.1',
    'category': 'Other',
    'description': """
Compassion Sponsorships Tracking
================================

Module to track the sponsorships.
It is based on a new state : sds_state.
It adds a new kanban, tree and form view to track sponsorships.

Color conventions for SDS Tracking Kanban View :

    0. Blank - Default color
    1. Black - Sponsorships with NO SUB (cancelled, or no_sub)
    2. Red - Sub_rejected sponsorships or sponsorships that are likely to
             become sub_reject.
    3. Yellow - Indicates a higher priority action is required on this
                sponsorship.
    4. Light green - Indicates an action is required on this sponsorship,
                     typically a mailing is to be sent to the sponsor.
                     This is a low priority action.
    5. Green - Sub_accepted sponsorships or sponsorships likely to become
               sub_accept.
    6. Light blue - not used
    7. Blue - Draft sponsorships
    8. Violet - not used
    9. Pink - not used
    """,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': [
        'message_center_compassion',
        ],
    'data': [
        'view/contract_view.xml',
        'workflow/sds_workflow.xml',
        'workflow/project_workflow.xml',
        'data/contract_cron.xml',
        'data/install.xml',
        ],
    'demo': [],
    'js': ['static/src/js/sponsorship_tracking_kanban.js'],
    'installable': True,
    'auto_install': False,
}
