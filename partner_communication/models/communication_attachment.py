
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

from odoo import api, models, fields
import logging


logger = logging.getLogger(__name__)


class CommunicationAttachment(models.Model):
    _name = 'partner.communication.attachment'
    _description = 'Communication Attachment'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(required=True)
    communication_id = fields.Many2one(
        'partner.communication.job', 'Communication', required=True,
        ondelete='cascade', readonly=False)
    report_id = fields.Many2one(
        'ir.actions.report', string='ID of report used by the attachment', readonly=False)
    report_name = fields.Char(
        required=True, help='Identifier of the report used to print')
    attachment_id = fields.Many2one(
        'ir.attachment', string="Attachments", required=True, readonly=False)
    data = fields.Binary(compute='_compute_data')

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

        if not vals.get('report_id'):
            vals['report_id'] = self.env['ir.actions.report']\
                ._get_report_from_name(vals.get('report_name')).id

        new_record = 'data' in vals and 'attachment_id' not in vals
        if new_record:
            name = vals['name']
            attachment = self.env['ir.attachment'].create({
                'datas_fname': name,
                'res_model': 'partner.communication.job',
                'datas': vals['data'],
                'name': name,
                'report_id': vals['report_id'],
            })
            vals['attachment_id'] = attachment.id

        res = super().create(vals)
        if new_record:
            res.attachment_id.res_id = res.communication_id.id
        return res

    @api.multi
    def print_attachments(self):
        total_attachment_with_omr = len(self.filtered(
            'attachment_id.enable_omr'
        ))
        count_attachment_with_omr = 1
        for attachment in self:
            # add omr to pdf if needed
            if attachment.communication_id.omr_enable_marks \
                    and attachment.attachment_id.enable_omr:
                is_latest_document = \
                    count_attachment_with_omr >= total_attachment_with_omr
                to_print = attachment.communication_id.add_omr_marks(
                    attachment.data, is_latest_document
                )

                count_attachment_with_omr += 1
            else:
                to_print = attachment.data

            report = self.env['ir.actions.report']\
                ._get_report_from_name(attachment.report_name)
            behaviour = report.behaviour()[report.id]
            printer = behaviour['printer']
            if behaviour['action'] != 'client' and printer:
                printer.with_context(
                    print_name=self.env.user.firstname[:3] + ' ' +
                    attachment.name
                ).print_document(
                    attachment.report_name, to_print, report.report_type)
        return True
