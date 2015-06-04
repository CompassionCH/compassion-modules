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
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
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


{
    'name': 'Add partner fields for Compassion',
    'version': '1.5',
    'category': 'Partner',
    'sequence': 150,
    'description': """
            Upgrade Partners to Compassion standards :
                1. Three lines for the address
                2. Mandatory reference sequence (CODEGA)
                3. Church members relation between Partners
                4. Birthdate and Deathdate
                5. Adds new contact titles
                6. Adds Partner Categories
                7. Notify on Partner Mandate changes
    """,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['base', 'partner_firstname', 'base_location',
                'email_template', 'account_banking_mandate'],
    'data': [
        'view/partner_compassion_view.xml',
        'data/partner_sequence.xml',
        'data/partner_title_data.xml',
        'data/partner_category_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
