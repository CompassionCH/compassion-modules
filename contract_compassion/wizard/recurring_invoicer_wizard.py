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

from openerp import api, models


class recurring_invoicer_wizard(models.TransientModel):
    _inherit = 'recurring.invoicer.wizard'

    @api.model
    def generate_from_cron(self):
        ret_dict = self.generate()
        invoicer = self.env['recurring.invoicer'].browse(ret_dict['res_id'])
        invoicer.validate_invoices()
