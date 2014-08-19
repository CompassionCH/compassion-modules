# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields, osv
from mysql_connector import mysql_connector
from openerp.tools.translate import _


class mysql_config(osv.osv_memory):
    _inherit = 'res.config.settings'
    _name = 'mysql.config.settings'
    
    _columns = {
        'default_mysql_host' : fields.char('MySQL Host', default_model='mysql.config.settings'),
        'default_mysql_db' : fields.char('MySQL Database', default_model='mysql.config.settings'),
        'default_mysql_user' : fields.char('MySQL User', default_model='mysql.config.settings'),
        'default_mysql_pw' : fields.char('MySQL Password', default_model='mysql.config.settings')
    }
    
    def execute(self, cr, uid, ids, context=None):
        super(mysql_config, self).execute(cr, uid, ids, context=context)
        mysql_test = mysql_connector(cr, uid, self)
        if not mysql_test.is_alive():
            raise osv.except_osv(_('Host not found'),
                                 _('Impossible to connect to the database.')
                                )
