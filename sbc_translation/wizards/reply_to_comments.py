from odoo import models, fields, api


class ReplyToComments(models.TransientModel):
    _name = "reply.to.comments"

    comments = fields.Char(string="Comments")
    answer = fields.Char(string="Answer")


    # @api.multi
    # def _get_comments(self):
    #     return self.env["correspondence"].browse(self.env.context.get("active_id")).comments
    #

    def send_reply(self):
        self.ensure_one()
