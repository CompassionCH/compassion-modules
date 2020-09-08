##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class CommunicationRevisionHistory(models.Model):
    _name = "partner.communication.revision.history"
    _rec_name = "revision_number"
    _description = "Communication template revision history"

    revision_number = fields.Float(required=True)
    revision_date = fields.Date(required=True)
    lang = fields.Selection(
        lambda self: self.env["res.lang"].sudo().get_installed(),
        "Language", required=True
    )
    subject = fields.Char()
    simplified_text = fields.Html(sanitize=False)
    body_html = fields.Html()
    linked_revision_id = fields.Many2one(
        comodel_name="partner.communication.revision",
        string="Revision history"
    )

    @api.multi
    def name_get(self):
        names = []
        for backup in self:
            name = "{:.2f}".format(round(backup.revision_number, 2))
            names.append((backup.id, name))
        return names

    def save_revision_state(self):
        self.ensure_one()
        self.write(self.linked_revision_id.read([
            "revision_number", "revision_date", "lang", "subject",
            "simplified_text", "body_html"
        ])[0])

    @api.multi
    def set_as_default_revision(self):
        self.linked_revision_id.restore_backup(self.revision_number)
