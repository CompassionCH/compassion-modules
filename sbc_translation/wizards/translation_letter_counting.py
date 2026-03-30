from odoo import api, fields, models

import datetime


class TranslationLetterCounting(models.TransientModel):
    _name = "translation.letter.counting.wizard"
    _description = "Counting of translation letters"

    name = fields.Char(default="Counting of translation letters")

    correspondence_ids = fields.Many2many(
        comodel_name="correspondence",
        string="Correspondences",
        compute="compute_correspondence_ids"
    )

    start_of_counting = fields.Datetime(
        string="Start of counting",
        help="Moment from which translated letters are counted",
    )

    counting = fields.Integer(
        string="Number of translated letters",
        compute="_compute_counting",
        help="Counting of the number of translated letters since the \"Start of counting\""
    )

    @api.model
    def init_wizard(self):
        # if a wizard already exists, we use it, else we create a new one
        wizard = self.search_active_wizard()
        if not wizard:
            wizard = self.env['translation.letter.counting.wizard'].create({
                'start_of_counting' : datetime.datetime.now()
            })
        return wizard

    @api.model
    def search_active_wizard(self):
        # Normally there should be maximum 1 wizard by user in the database.
        # In case of multiple wizard in the database, we consider only the first one
        return self.search([('create_uid', '=', self.env.uid)], limit=1)

    @api.model
    def action_open_wizard(self):
        wizard = self.init_wizard()
        return {
            'name': 'Counting of translation letters',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'translation.letter.counting.wizard',
            'res_id': wizard.id
        }

    @api.depends('start_of_counting')
    def compute_correspondence_ids(self):
        correspondence_ids = self.env["correspondence"].search(
            [
                ("translate_done", ">=", self.start_of_counting)
            ]
        )
        self.correspondence_ids  = [(6, 0, correspondence_ids)]

    @api.depends("correspondence_ids")
    def _compute_counting(self):
        self.counting = len(self.correspondence_ids)
