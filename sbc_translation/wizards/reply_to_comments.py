from odoo import models, fields, api


class ReplyToComments(models.TransientModel):
    _name = "reply.to.comments"

    paragraph_ids = fields.Many2many(
        "correspondence.paragraph", string="Paragraphs", readonly=True)
    answer = fields.Char(string="Answer")

    def send_reply(self):
        self.ensure_one()
        print("Reply SENDED")
        return True


