##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class CorrespondenceTemplatePage(models.Model):
    _name = "correspondence.template.page"
    _description = "Correspondence template page"
    _order = "template_id asc, page_index asc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    template_id = fields.Many2one(
        "correspondence.template",
        "Template",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=False,
    )
    page_index = fields.Integer(required=True, default=1)
    name = fields.Char(compute="_compute_name")
    background = fields.Image("Page background", help="Use 300 DPI images")
    header_box_id = fields.Many2one(
        "correspondence.text.box", string="Header", readonly=False
    )
    text_box_ids = fields.Many2many(
        "correspondence.text.box",
        "correspondence_text_boxes_rel",
        string="Text boxes",
        readonly=False,
    )
    image_box_ids = fields.Many2many(
        "correspondence.positioned.object",
        "correspondence_image_boxes_rel",
        string="Image boxes",
        readonly=False,
    )

    _sql_constraints = [
        (
            "unique_page",
            "unique(template_id,page_index)",
            "This page is already defined. Change the index.",
        )
    ]

    @api.onchange("template_id")
    def onchange_template_id(self):
        self.page_index = len(self.template_id.page_ids)

    def _compute_name(self):
        for page in self:
            page.name = (
                page.template_id.name + " " + _("Page") + " " + str(page.page_index)
            )
