##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import models, fields


class ProjectCovidStatus(models.Model):
    _name = "compassion.project.covid_update"
    _description = "Project covid status"
    _order = "update_date,id desc"

    fcp_id = fields.Many2one(
        "compassion.project", required=True, ondelete="cascade"
    )
    update_date = fields.Date("updated on", default=fields.Date.today)
    re_opening_status = fields.Char()
    comments = fields.Char()
