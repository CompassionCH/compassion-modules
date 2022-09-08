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
import base64

from odoo import models, fields
from odoo.tools.pdf import merge_pdf

_logger = logging.getLogger(__name__)


class DownloadPrintJobWizard(models.TransientModel):
    _name = "partner.communication.download.print.job.wizard"
    _description = "Partner Communication - Download Print Job Wizard"

    communication_job_ids = fields.Many2many(
        "partner.communication.job", "partner_communication_download_print_rel", string="Letters", required=True,
        readonly=True
    )
    attachment_ids = fields.One2many(
        "partner.communication.attachment", string="Attachments", compute="_compute_attachment_ids")
    merged_data = fields.Binary(compute="_compute_merged_data")
    merged_name = fields.Char(compute="_compute_merge_name")

    def _compute_attachment_ids(self):
        for wiz in self:
            wiz.attachment_ids = wiz.communication_job_ids.mapped("attachment_ids")

    def _compute_merged_data(self):
        for wiz in self:
            pdf_data = []
            for job in wiz.mapped("communication_job_ids"):
                pdf_data.append(base64.b64decode(job.printed_pdf_data))
                attachments = job.attachment_ids.filtered(
                    lambda a: a.printed_pdf_data and a.attachment_id.mimetype == "application/pdf")
                if attachments:
                    pdf_data.extend(attachments.mapped(lambda a: base64.b64decode(a.printed_pdf_data)))
            wiz.merged_data = base64.b64encode(merge_pdf(pdf_data))

    def _compute_merge_name(self):
        for wiz in self:
            wiz.merged_name = fields.Datetime.to_string(fields.Datetime.now()) + " - Odoo communication print.pdf"

    def clear_data(self):
        self.mapped("communication_job_ids.attachment_ids").write({"printed_pdf_data": False})
        self.mapped("communication_job_ids").write({"printed_pdf_data": False})
        return True
