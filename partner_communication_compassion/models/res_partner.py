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

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """

    _inherit = "res.partner"

    letter_delivery_preference = fields.Selection(
        selection="_get_delivery_preference",
        default="auto_digital",
        required=True,
        help="Delivery preference for Child Letters",
    )
    photo_delivery_preference = fields.Selection(
        selection="_get_delivery_preference",
        default="both",
        required=True,
        help="Delivery preference for Child photo",
    )
