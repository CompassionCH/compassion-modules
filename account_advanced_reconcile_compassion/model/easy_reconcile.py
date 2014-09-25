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

from openerp.osv import orm


class account_easy_reconcile_method(orm.Model):

    _inherit = 'account.easy.reconcile.method'

    def _get_all_rec_method(self, cr, uid, context=None):
        methods = super(account_easy_reconcile_method, self).\
            _get_all_rec_method(cr, uid, context=context)
        methods += [
            ('easy.reconcile.advanced.bvr_ref',
             'Advanced. BVR Ref. Compassion'),
        ]
        return methods
