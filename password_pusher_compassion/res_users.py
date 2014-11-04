# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.osv import fields, orm
import gp_connector


class res_users(orm.Model):
    """ This class pushes the passwords of users to the MySQL database of GP
        upon modification. """
    _inherit = "res.users"

    def get_pw(self, cr, uid, ids, name, args, context):
        return super(res_users, self).get_pw(cr, uid, ids, name, args,
                                             context)

    def set_pw2(self, cr, uid, id, name, value, args, context):
        if value:
            gp = gp_connector.GPConnect(cr, uid)
            gp.pushPassword(id, value)
            super(res_users, self).set_pw(
                cr, uid, id, name, value, args, context)

    _columns = {
        'password': fields.function(
            get_pw, fnct_inv=set_pw2, type='char', string='Password',
            invisible=True, store=True),
    }
