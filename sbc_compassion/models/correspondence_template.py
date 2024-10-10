##############################################################################
#
#    Copyright (C) 2014-2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CorrespondenceTemplate(models.Model):
    """This class defines a template used for Supporter Letters and holds
    all information relative to position of metadata in the Template.

    Template images should be in 300 DPI
    """

    _name = "correspondence.template"
    _description = "Correspondence template"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(required=True, translate=True)
    type = fields.Selection(
        [
            ("s2b", "S2B Template"),
            ("b2s", "B2S Layout"),
        ],
        required=True,
        default="s2b",
    )
    active = fields.Boolean(default=True)
    layout = fields.Selection(
        [
            ("CH-A-1S11-1", "Layout 1"),
            ("CH-A-2S01-1", "Layout 2"),
            ("CH-A-3S01-1", "Layout 3"),
            ("CH-A-4S01-1", "Layout 4"),
            ("CH-A-5S01-1", "Layout 5"),
            ("CH-A-6S11-1", "Layout 6"),
        ]
    )
    template_image = fields.Image(
        compute="_compute_template_image", max_width=500, max_height=500
    )
    usage_count = fields.Integer(compute="_compute_usage_count")
    page_ids = fields.One2many(
        "correspondence.template.page",
        "template_id",
        "Pages",
        required=True,
        copy=True,
        readonly=False,
        domain=[("page_index", "<", 3)],
    )
    additional_page_id = fields.Many2one(
        "correspondence.template.page",
        "Additional page",
        help="Template used in case the S2B text is too long to fit on the "
        "standard two-sided page.",
        readonly=False,
        domain=[("page_index", ">", 2)],
    )

    def _compute_usage_count(self):
        for template in self:
            template.usage_count = self.env["correspondence"].search_count(
                [("template_id", "=", template.id)]
            )

    def _compute_template_image(self):
        for template in self:
            template.template_image = template.page_ids[:1].background
