##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Daniel Gergely <dgergely@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class ResPartnerSegmentLink(models.Model):
    """
    Model to store the
    - URL
    - Label
    - Language
    - Category
    of a partner segmentation link, which then can be used to
    provide useful links to the partners based on their segmentation
    category and language.
    """

    _name = "res.partner.segment.link"
    _description = "Partner Segmentation Link"

    url = fields.Char(
        required=True, help="URL of the link to be provided to the partner"
    )
    label = fields.Char(
        required=True, help="Label of the link to be provided to the partner"
    )
    language_id = fields.Many2one(
        "res.lang",
        string="Language",
        help="Language of the link, used to provide the link to the partner based on their language",
    )
    category_id = fields.Many2one(
        "res.partner.segment",
        string="Category",
        help="Segmentation category of the link, used to provide the link to the partner based on their segmentation category",
    )
