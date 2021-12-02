# Copyright (C) 2021 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class IgnoredReporter(models.Model):
    _name = 'ignored.reporter'
    _order = "email asc"

    email = fields.Char(required=True)
