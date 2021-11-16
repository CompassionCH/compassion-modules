# Copyright (C) 2021 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, _, fields


class IgnoredReporter(models.Model):
    """

    """
    _name = 'ignored_reporter'
    _order = "email asc"

    email = fields.Char()
