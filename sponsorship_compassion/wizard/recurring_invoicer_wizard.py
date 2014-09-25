# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm


class recurring_invoicer_wizard(orm.TransientModel):
    _inherit = 'recurring.invoicer.wizard'

    def generate_from_cron(self, cr, uid, group=False, context=None):
        ret_dict = self.generate(cr, uid, [], context=context, group=group)
        recurring_invoicer_obj = self.pool.get('recurring.invoicer')
        recurring_invoicer_obj.validate_invoices(cr, uid, [ret_dict['res_id']])
