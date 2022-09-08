from odoo import models, fields


class DeConfig(models.AbstractModel):
    _inherit = "partner.communication.defaults"

    omr_enable_marks = fields.Boolean(
        string="Enable OMR",
        help="If set to True, the OMR marks are displayed in the communication.",
    )
    omr_should_close_envelope = fields.Boolean(
        string="OMR should close the envelope",
        help="If set to True, the OMR mark for closing the envelope is added "
        "to the communication.",
    )
    omr_add_attachment_tray_1 = fields.Boolean(
        string="Attachment from tray 1",
        help="If set to True, the OMR mark for adding an "
        "attachment from back 1 is added to the communication.",
    )
    omr_add_attachment_tray_2 = fields.Boolean(
        string="Attachment from tray 2",
        help="If set to True, the OMR mark for adding an "
        "attachment from tray 2 is added to the communication.",
    )
    omr_top_mark_x = fields.Float(
        default=7, help="X position in millimeters of the first OMR mark in the page"
    )
    omr_top_mark_y = fields.Float(
        default=190,
        help="Y position in millimeters of the first OMR mark in the page, "
        "computed from the bottom of the page.",
    )
    omr_single_sided = fields.Boolean(
        help="Will put the OMR marks on every page if the document is printed "
        "single-sided."
    )
