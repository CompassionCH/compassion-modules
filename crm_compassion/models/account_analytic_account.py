##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class AnalyticAccount(models.Model):
    """Add year in name of analytic accounts."""

    _inherit = "account.analytic.account"

    year = fields.Char()
    event_id = fields.Many2one(
        "crm.event.compassion", "Event", store=True, readonly=True
    )

    def name_get(self):
        res = []
        for analytic in self:
            name = analytic.name
            if analytic.code:
                name = "[" + analytic.code + "] " + name
            if analytic.year and not name.endswith(analytic.year):
                name = name + " " + analytic.year
            res.append((analytic.id, name))
        return res
