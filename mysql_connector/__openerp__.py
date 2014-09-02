# -*- coding: utf-8 -*-
##############################################################################
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
    'name': 'OpenERP MySQL Connector',
    'version': '1.0.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': [],
    'external_dependencies': {
        'python': ['MySQLdb'],
    },
    'description': """ 

OpenERP MySQL Connector
=========================

Utility module that enables other modules that depends on it to access a MySQL server that is defined a settings screen.

Warning : This module requires python-MySQLdb to be installed on the server.
""",
    'data': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
