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

    @api.model_create_multi
    def create(self, vals_list):
        notes = super().create(vals_list)
        for note in notes:
            note.child_id.message_post(
                body=note.body, subject=_("New beneficiary notes")
            )
        return notes

    @api.model
    def process_commkit(self, commkit_data):
        note_ids = list()
        for notes_data in commkit_data.get("GPPublicNotesKit", [commkit_data]):
            if notes_data.get("RecordType") == "ICP":
                # FCP notes reference the project (ICP_ID) instead of a child
                note_ids += self._process_fcp_note(notes_data)
                continue
            vals = self.json_to_data(notes_data)
            child_note = self.create(vals)
            note_ids.append(child_note.id)
        return note_ids

    @api.model
    def _process_fcp_note(self, notes_data):
        """Post a note received for an FCP in the chatter of the project.
        :return: list with the project id, empty if the project is unknown
        """
        project = self.env["compassion.project"].search(
            [("fcp_id", "=", notes_data.get("GlobalID"))], limit=1
        )
        if project and notes_data.get("Body"):
            project.message_post(body=notes_data["Body"], subject=_("New FCP notes"))
        return project.ids
