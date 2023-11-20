##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class CommunicationRevisionHistory(models.Model):
    _name = "partner.communication.revision.history"
    _rec_name = "revision_number"
    _description = "Communication template revision history"
    _order = "linked_revision_id desc,revision_number desc"

    revision_number = fields.Float(required=True, index=True)
    revision_date = fields.Date(required=True)
    subject = fields.Char()
    raw_subject = fields.Char()
    body_html = fields.Html(sanitize=False)
    linked_revision_id = fields.Many2one(
        comodel_name="partner.communication.revision",
        string="Revision history",
        required=True,
        index=True,
        ondelete="cascade",
    )
    proposition_text = fields.Html()

    _sql_constraints = [
        (
            "unique_version",
            "unique(linked_revision_id,revision_number)",
            "This version is already existing!",
        )
    ]

    def name_get(self):
        names = []
        for backup in self:
            name = f"{round(backup.revision_number, 2):.2f}"
            names.append((backup.id, name))
        return names

    def save_revision_state(self):
        write_fields = ["revision_number", "revision_date", "body_html", "raw_subject"]
        if self.linked_revision_id.state == "active":
            # Also change revision texts when they are not being edited
            write_fields += ["proposition_text", "subject"]
        for revision in self:
            revision.write(revision.linked_revision_id.read(write_fields)[0])

    def get_vals(self):
        read_fields = ["revision_number", "revision_date", "body_html", "raw_subject"]
        if self.linked_revision_id.state == "active":
            # Also change revision texts when they are not being edited
            read_fields += ["proposition_text", "subject"]
        vals = self.read(read_fields)[0]
        vals.pop("id")
        return vals
