# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, _


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def open_events(self):
        event_ids = self.env['crm.event.compassion'].search(
            [('partner_id', 'child_of', self.ids)]).ids

        return {
            'name': _('Events'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'crm.event.compassion',
            'target': 'current',
            'domain': [('id', 'in', event_ids)],
        }
