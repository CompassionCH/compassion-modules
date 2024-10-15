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
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino
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
    "name": "Reminder for contracts",
    "summary": "Reminder features",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Compassion CH",
    "development_status": "Production/Stable",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "category": "Accounting",
    "depends": ["partner_communication", "recurring_contract", "child_compassion"],
    "external_dependencies": {},
    "data": [
        "data/email_reminder_template.xml",
        "data/contract_reminder.xml",
    ],
    "installable": True,
}
