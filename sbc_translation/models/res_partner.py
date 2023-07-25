##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import functools
import random
import string
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    translation_user_id = fields.One2many(
        "translation.user",
        inverse_name="partner_id",
        string="Translation User",
        help="Allow to engage the partner in translations.")

    _sql_constraints = [
        ('translation_user_uniq', 'check(translation_user_id)', 'Only one Translation User can be linked !'),
    ]
