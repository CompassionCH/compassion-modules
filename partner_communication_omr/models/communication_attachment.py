##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, fields

logger = logging.getLogger(__name__)


class CommunicationAttachment(models.Model):
    _inherit = "partner.communication.attachment"

    is_last_to_print = fields.Boolean(
        help="Technical field for identifying last printed document with OMR marks."
    )

    def print_attachments(self, output_tray=None):
        self.filtered("attachment_id.enable_omr")[-1:].is_last_to_print = True
        return super().print_attachments(output_tray)

    def _get_attachment_data(self):
        # add omr to pdf if needed
        if self.communication_id.omr_enable_marks and self.attachment_id.enable_omr:
            return self.communication_id.add_omr_marks(self.data, self.is_last_to_print)
        else:
            return super()._get_attachment_data()
