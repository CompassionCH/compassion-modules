
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class IrAttachment(models.Model):
    """ Add a link to report to know how to print the attachment. """
    _inherit = 'ir.attachment'

    report_id = fields.Many2one(
        'ir.actions.report', 'Print configuration',
        domain=[('property_printing_action_id.action_type', '=', 'server')], readonly=False
    )
    enable_omr = fields.Boolean(
        string="Enable OMR",
        help="If checked, the OMR marks will be print on the document",
        default=True
    )
