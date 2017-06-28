# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from odoo import api, models, _


class QueueJob(models.Model):
    _inherit = 'queue.job'

    @api.multi
    def related_action_contracts(self):
        action = {
            'name': _("Contracts"),
            'type': 'ir.actions.act_window',
            'res_model': 'recurring.contract',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.record_ids)],
        }
        return action
