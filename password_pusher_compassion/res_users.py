# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino. Copyright Compassion Suisse
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
from openerp.osv.orm import Model, fields
from openerp.osv import fields, osv
import gp_connector


class res_users(osv.osv):
    """ This class pushes the passwords of users to the MySQL database of GP upon modification. """
    _inherit = "res.users"
    
    def get_pw( self, cr, uid, ids, name, args, context ):
        return super(res_users, self).get_pw(cr, uid, ids, name, args, context)
        
    def set_pw2(self, cr, uid, id, name, value, args, context):
        if value:
            gp = gp_connector.GPConnect(cr, uid, self.pool.get('mysql.config.settings'))
            gp.pushPassword(id, value)
            super(res_users, self).set_pw(cr, uid, id, name, value, args, context)
            
    _columns = {
        'password': fields.function(get_pw, fnct_inv=set_pw2, type='char', string='Password', invisible=True, store=True),
    }
res_users()