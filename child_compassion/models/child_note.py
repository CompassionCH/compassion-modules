##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import _, api, fields, models


class ChildNote(models.Model):
    """A child Note"""

    _name = "compassion.child.note"
    _description = "Child Note"
    _order = "id desc"
    _inherit = ["compassion.mapped.model"]

    child_id = fields.Many2one(
        "compassion.child", "Child", required=True, ondelete="cascade", readonly=False
    )
    body = fields.Char()
    record_type = fields.Char()
    type = fields.Char()
    visibility = fields.Char()
    source_code = fields.Char()

    @api.model
    def create(self, vals):
        note = super().create(vals)
        note.child_id.message_post(body=note.body, subject=_("New beneficiary notes"))
        return note

    @api.model
    def process_commkit(self, commkit_data):
        note_ids = list()
        for notes_data in commkit_data.get("GPPublicNotesKit", [commkit_data]):
            vals = self.json_to_data(notes_data)
            child_note = self.create(vals)
            note_ids.append(child_note.id)
        return note_ids
