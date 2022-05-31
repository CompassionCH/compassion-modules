##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class PhoneCall(models.Model):
    _inherit = "crm.phonecall"

    is_from_employee = fields.Boolean(default=False)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if "origin" in self._context and \
                self._context.get('origin') == 'employee':
            res.is_from_employee = True
        return res

    @api.multi
    def write(self, values):
        """ Mark any linked activities as done. """
        super().write(values)
        if values.get("state") == "done" and not self.env.context.get("from_activity"):
            for phonecall in self:
                activity = self.env["mail.activity"].search([("phonecall_id", "=", phonecall.id)])
                if activity:
                    activity.action_feedback(feedback=phonecall.description)
        return True
