from odoo import api, models


class GmcMessagePoolProcess(models.TransientModel):
    _name = 'gmc.message.process'
    _description = 'GMC Pool Process Wizard'

    @api.multi
    def process_messages(self):
        active_ids = self.env.context.get('active_ids', [])
        self.env['gmc.message'].browse(active_ids).process_messages()
        action = {
            'name': 'Message treated',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'views': [(False, 'tree'), (False, 'form')],
            'res_model': 'gmc.message',
            'domain': [('id', 'in', active_ids)],
            'target': 'current',
        }

        return action
