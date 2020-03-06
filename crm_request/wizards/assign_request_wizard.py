# Copyright (C) 2019 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AssignRequestWizard(models.TransientModel):
    _name = 'assign.request.wizard'
    _description = 'Request Assignation Wizard'

    user_id = fields.Many2one('res.users', 'Assign to',
                              default=lambda self: self.env.user, readonly=False)
    intern_note = fields.Text('Internal note')

    @api.multi
    def assign_to(self):
        self.ensure_one()
        model = self.env.context.get('active_model')
        model_id = self.env.context.get('active_id')
        request = self.env[model].browse(model_id)
        request.user_id = self.user_id
        if self.intern_note:
            request.message_post(subject='Message for ' + self.user_id.name,
                                 body=self.intern_note)
