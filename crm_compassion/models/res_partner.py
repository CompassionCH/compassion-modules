# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, _


class Partner(models.Model):
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

    @api.multi
    def make_ambassador(self):
        portal = self.env['portal.wizard'].create({})
        portal.onchange_portal_id()
        users = portal.mapped('user_ids')
        users.write({'in_portal': True})
        no_mail = users.filtered(lambda u: not u.email)
        for user in no_mail:
            partner = user.partner_id
            user.email = partner.firstname[0].lower() + \
                partner.lastname.lower() + '@cs.local'
        portal.action_apply()
        no_mail.mapped('partner_id').write({'email': False})
        return True
