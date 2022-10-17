##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class ResPartnerTitle(models.Model):
    """
    Adds salutation and gender fields.
    """

    _inherit = ["res.partner.title", "translatable.model"]
    _name = "res.partner.title"
    _order = "order_index ASC, name ASC"

    plural = fields.Boolean()
    order_index = fields.Integer()
