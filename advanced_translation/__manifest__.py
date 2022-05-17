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
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
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
    "name": "Advanced Translation",
    "version": "14.0.1.0.0",
    "category": "Other",
    "sequence": 150,
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "development_status": "Stable",
    "depends": ["base"],
    "external_dependencies": {"python": ["babel", "pytesseract", "iso639",
                                         "langdetect"]},
    "data": [
        "security/ir.model.access.csv",
        "views/advanced_translation_view.xml",
        "data/res.lang.compassion.csv",
        "data/ir.advanced.translation.csv",
    ],
    "demo": ["demo/ir.advanced.translation.csv"],
    "installable": True,
    "auto_install": False,
}
