# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import osv
import base64


class mail_thread(osv.AbstractModel):
    """ This class adds a method to mail_thread in order to easily post
    messages from GP."""

    _inherit = 'mail.thread'

    def message_post_from_gp(self, cr, uid, model, thread_id, body='',
                             subject=None, attachments=None):
        # If any attachments, decode them, as it is send over XML
        decodedAttachments = []
        if (attachments):
            for name, content in attachments:
                decoded = (name, base64.b64decode(str(content)))
                decodedAttachments.append(decoded)

        return self.message_post(
            cr, uid, thread_id, body, subject, 'comment', None, False,
            decodedAttachments, {'thread_model': model}, 'html')
