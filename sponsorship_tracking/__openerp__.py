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
Module to track the sponsorships.
It is based on a new state :sds_state.
It adds a new tree and form view to track sponsorships.
    """,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': [
        'sponsorship_compassion',
        ],
    'data': [
        'view/contract_view.xml',
        'view/project_view.xml',
        'workflow/contract_workflow.xml',
        'workflow/project_workflow.xml',
        'data/contract_cron.xml',
        'data/install.xml',
        ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
