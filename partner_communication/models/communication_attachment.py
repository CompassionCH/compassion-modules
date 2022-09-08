##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging

from odoo import api, models, fields

logger = logging.getLogger(__name__)


class CommunicationAttachment(models.Model):
    _name = "partner.communication.attachment"
    _description = "Communication Attachment"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(required=True)
    communication_id = fields.Many2one(
        "partner.communication.job",
        "Communication",
        required=True,
        ondelete="cascade",
        readonly=False,
    )
    report_id = fields.Many2one(
        "ir.actions.report",
        string="ID of report used by the attachment",
        readonly=False,
    )
    report_name = fields.Char(
        required=True, help="Identifier of the report used to print"
    )
    attachment_id = fields.Many2one(
        "ir.attachment", string="Attachments", required=True, readonly=False, ondelete="cascade"
    )
    data = fields.Binary(compute="_compute_data")
    printed_pdf_data = fields.Binary(
        help="Technical field used when the report was not sent to printer but to client "
             "in order to download the result afterwards."
    )
    printed_pdf_name = fields.Char(related="attachment_id.name")

    def _compute_data(self):
        for attachment in self:
            attachment.data = base64.b64decode(attachment.attachment_id.datas)

    @api.model
    def create(self, vals):
        """
        Allows to send binary data for attachment instead of record.
        :param vals: vals for creation
        :return: record created
        """

        if not vals.get("report_id"):
            vals["report_id"] = (
                self.env["ir.actions.report"]
                    ._get_report_from_name(vals.get("report_name"))
                    .id
            )

        new_record = "data" in vals and "attachment_id" not in vals
        if new_record:
            name = vals["name"]
            attachment = self.env["ir.attachment"].create(
                {
                    "res_model": "partner.communication.job",
                    "datas": vals["data"],
                    "name": name,
                    "report_id": vals["report_id"],
                }
            )
            vals["attachment_id"] = attachment.id

        res = super().create(vals)
        if new_record:
            res.attachment_id.res_id = res.communication_id.id
        return res

    def unlink(self):
        attachments = self.mapped("attachment_id")
        super().unlink()
        attachments.unlink()
        return True

    def print_attachments(self, output_tray=None):
        for attachment in self:
            report = self.env["ir.actions.report"]._get_report_from_name(
                attachment.report_name
            ).with_context(
                lang=attachment.communication_id.partner_id.lang)
            behaviour = report.behaviour()
            printer = behaviour.pop("printer", False)
            data = attachment._get_attachment_data()
            if behaviour.pop("action", "client") != "client" and printer:
                print_options = {opt: value for opt, value in behaviour.items() if
                                 value}
                if output_tray:
                    print_options["output_tray"] = output_tray
                printer.with_context(
                    print_name=self.env.user.name[:3] + " " + attachment.name,
                ).print_document(attachment.report_name, data, **print_options)
            else:
                attachment.printed_pdf_data = base64.b64encode(data)
        return True

    def _get_attachment_data(self):
        """
        Hook for retrieving what we want to print for each communication attachment.
        """
        self.ensure_one()
        return self.data
