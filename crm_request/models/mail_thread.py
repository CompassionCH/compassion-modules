
import email
from email.message import Message
from odoo.tools import pycompat

from odoo import api, models, tools


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def message_parse(self, message, save_original=False):
        msg_dict = super().message_parse(message, save_original)
        if not isinstance(message, Message):
            # message_from_string works on a native str
            message = pycompat.to_native(message)
            message = email.message_from_string(message)
        msg_dict['reply_to'] = tools.decode_smtp_header(message.get('Reply-To'))
        return msg_dict
