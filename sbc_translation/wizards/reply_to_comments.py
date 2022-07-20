from odoo import models, fields, api


class ReplyToComments(models.TransientModel):
    _name = "reply.to.comments"

    paragraph_ids = fields.Many2many("correspondence.paragraph", string="Paragraphs", readonly=True)
    answer = fields.Text(string="Answer")

    @api.multi
    def send_reply(self):
        corr = self.env['correspondence'].search([('id', '=', self._context['active_id'])])
        return corr.reply_to_comments(self.answer)

