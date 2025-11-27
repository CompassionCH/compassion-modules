from odoo import api, models, tools


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def message_parse(self, message, save_original=False):
        msg_dict = super().message_parse(message, save_original)
        if "reply_to" not in msg_dict:
            msg_dict["reply_to"] = tools.decode_message_header(message, "Reply-To")
        return msg_dict
