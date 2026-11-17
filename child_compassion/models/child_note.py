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
        "compassion.child", "Child", ondelete="cascade", readonly=False, index=True
    )
    # Notes received for an FCP (RecordType ICP) are linked to the project
    project_id = fields.Many2one(
        "compassion.project", "FCP", ondelete="cascade", readonly=False, index=True
    )
    body = fields.Char()
    record_type = fields.Char()
    type = fields.Char()
    visibility = fields.Char()
    source_code = fields.Char()

    _sql_constraints = [
        (
            "child_or_project",
            "CHECK(child_id IS NOT NULL OR project_id IS NOT NULL)",
            "A note must be linked to a child or an FCP.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        notes = super().create(vals_list)
        for note in notes:
            if note.child_id:
                note.child_id.message_post(
                    body=note.body, subject=_("New beneficiary notes")
                )
            elif note.project_id:
                note.project_id.message_post(body=note.body, subject=_("New FCP notes"))
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
        """Store a note received for an FCP on the project.
        :return: list with the note id, empty if the project is unknown
        """
        project = self.env["compassion.project"].search(
            [("fcp_id", "=", notes_data.get("GlobalID"))], limit=1
        )
        if not project:
            return []
        note = self.create(
            {
                "project_id": project.id,
                "body": notes_data.get("Body"),
                "record_type": notes_data.get("RecordType"),
                "type": notes_data.get("Type"),
                "visibility": notes_data.get("Visibility"),
                "source_code": notes_data.get("SourceKitName"),
            }
        )
        return note.ids
