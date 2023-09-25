from odoo import api, fields, models


class ReplyToComments(models.TransientModel):
    _name = "sbc.reply.to.comments.wizard"

    paragraph_ids = fields.Many2many(
        "correspondence.paragraph", string="Paragraphs", readonly=True
    )
    answer = fields.Html()

    @api.multi
    def send_reply(self):
        corr = self.env["correspondence"].browse(self.env.context.get("active_id"))
        return corr.reply_to_comments(self.answer)
