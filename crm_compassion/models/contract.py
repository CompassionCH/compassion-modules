##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _


class Contracts(models.Model):
    """ Adds the Salesperson to the contract. """

    _inherit = "recurring.contract"

    user_id = fields.Many2one("res.partner", "Ambassador", readonly=False)

    @api.onchange("origin_id")
    def on_change_origin(self):
        origin = self.origin_id
        if origin:
            ambassador = self._get_user_from_origin(origin)
            if ambassador:
                self.user_id = ambassador

    @api.onchange("child_id")
    def onchange_child_id(self):
        hold = self.hold_id
        origin = hold.origin_id
        if origin:
            self.origin_id = origin
        if hold.channel and hold.channel == "web":
            self.channel = "internet"
        if hold.ambassador:
            self.user_id = hold.ambassador
        self.campaign_id = hold.campaign_id
        if hold.comments:
            return {
                "warning": {
                    "title": _("The child has some comments"),
                    "message": hold.comments,
                }
            }

    def _get_user_from_origin(self, origin):
        user_id = False
        if origin.partner_id:
            user_id = origin.partner_id.id
        elif origin.event_id and origin.event_id.user_id:
            user_id = origin.event_id.user_id.partner_id.id
        elif origin.analytic_id and origin.analytic_id.partner_id:
            user_id = origin.analytic_id.partner_id.id
        return user_id

    def get_inv_lines_data(self):
        res = super().get_inv_lines_data()
        for i, c_line in enumerate(self.mapped("contract_line_ids")):
            if c_line.contract_id.user_id:
                res[i]["user_id"] = c_line.contract_id.user_id.id
        return res
