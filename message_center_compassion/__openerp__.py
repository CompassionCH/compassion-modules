# -*- coding: utf-8 -*-
##############################################################################
#    Author : Emanuel Cino
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Compassion CH Message Center',
    'version': '0.5.0',
    'category': 'Other',
    'description': """
        Message Center that offers a queue of messages that have to be sent
        to GMC and a queue of messages received from GMC.

        Warning : this addon requires the python-requests library to be
        installed on the server. (sudo apt-get install python-requests).
    """,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['sponsorship_compassion', 'partner_firstname'],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'view/gmc_message_view.xml',
        'data/gmc_action.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
