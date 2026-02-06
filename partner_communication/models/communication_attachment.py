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

from odoo import api, fields, models

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
    )
    report_id = fields.Many2one(
        "ir.actions.report",
        string="ID of report used by the attachment",
    )
    report_name = fields.Char(
        required=True, help="Identifier of the report used to print"
    )
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Attachments",
        required=True,
        ondelete="cascade",
    )
    data = fields.Binary(compute="_compute_data")
    printed_pdf_data = fields.Binary(
        help="Technical field used when the report was not sent to printer "
        "but to client in order to download the result afterwards."
    )
    printed_pdf_name = fields.Char(related="attachment_id.name")

    def _compute_data(self):
        for attachment in self:
            attachment.data = base64.b64decode(attachment.attachment_id.datas)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Get the technical name (e.g., 'partner_communication.a4_communication')
            r_name = vals.get("report_name")

            if r_name:
                report = self.env["ir.actions.report"]._get_report_from_name(r_name)
                if report:
                    vals["report_id"] = report.id
                    # Ensure the value is in the dict for the SQL INSERT
                    vals["report_name"] = r_name

                    # POP the heavy data to prevent the 'S' / Type error
            binary_data = vals.pop("data", None) or vals.pop("datas", None)

            if binary_data and not vals.get("attachment_id"):
                attachment = self.env["ir.attachment"].create({
                    "res_model": "partner.communication.job",
                    "datas": binary_data,
                    "name": vals.get("name"),
                    "type": "binary",
                })
                vals["attachment_id"] = attachment.id

        # Odoo will now include 'report_name' in the INSERT if it's defined in the class
        return super().create(vals_list)

    def unlink(self):
        attachments = self.mapped("attachment_id")
        super().unlink()
        attachments.unlink()
        return True

    def print_attachments(self, output_tray=None):
        for attachment in self:
            report = (
                self.env["ir.actions.report"]
                ._get_report_from_name(attachment.report_name)
                .with_context(lang=attachment.communication_id.partner_id.lang)
            )
            behaviour = report.behaviour()
            printer = behaviour.pop("printer", False)
            data = attachment._get_attachment_data()
            if behaviour.pop("action", "client") != "client" and printer:
                print_options = {
                    opt: value for opt, value in behaviour.items() if value
                }
                if output_tray:
                    print_options["output_tray"] = output_tray
                printer.with_context(
                    print_name=self.env.user.name[:3] + " " + attachment.name,
                ).print_document(attachment.report_id, data, **print_options)
            else:
                attachment.printed_pdf_data = base64.b64encode(data)
        return True

    def _get_attachment_data(self):
        """
        Hook for retrieving what we want to print for each communication attachment.
        """
        self.ensure_one()
        return self.data
