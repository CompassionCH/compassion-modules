# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino. Copyright Compassion Suisse
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv, orm
from openerp.osv.orm import browse_record, browse_null
import base64
import pdb

class mail_thread(osv.AbstractModel):
    """ This class adds a method to mail_thread in order to easily post messages from GP."""

    _inherit = 'mail.thread'
    
    def message_post_from_gp(self, cr, uid, thread_id, body='', subject=None, attachments=None):
        # If any attachments, decode them, as it is send over XML
        decodedAttachments = []
        if (attachments):
            for name, content in attachments:
                decoded = (name, base64.b64decode(str(content)))
                decodedAttachments.append(decoded)
        
        return super(mail_thread, self).message_post(cr, uid, thread_id, body, subject, 'comment', None, False, decodedAttachments, {'thread_model':'res.partner'}, 'html')
    