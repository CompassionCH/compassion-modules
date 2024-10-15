##############################################################################
#
#    Copyright (C) 2017-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class ResCountry(models.Model):
    _inherit = "res.country"

    in_preposition = fields.Char(translate=True, default="in")
    from_preposition = fields.Char(translate=True, default="from")
