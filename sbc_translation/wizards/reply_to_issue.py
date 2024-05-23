from odoo import fields, models


class ReplyToIssue(models.TransientModel):
    _name = "sbc.reply.to.issue.wizard"

    translation_issue = fields.Selection(
        selection="forward_get_translation_issue_list",
        string="Issue type",
        readonly=True
    )

    translation_issue_comments = fields.Html(
        string="Issue comment",
        readonly=True
    )

    answer = fields.Html()

    def send_reply(self):
        corr = self.env["correspondence"].browse(
            self.env.context.get("active_id")
        )
        return corr.reply_to_issue(self.answer)

    def forward_get_translation_issue_list(self):
        return self.env["correspondence"].get_translation_issue_list()

