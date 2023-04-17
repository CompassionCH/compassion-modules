##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models


class PortalWizard(models.TransientModel):
    """This class creates analytic accounts for new portal users."""

    _inherit = "portal.wizard"

    def action_apply(self):
        self.ensure_one()
        res = super().action_apply()
        for user in self.user_ids:
            users = (
                self.env["res.users"]
                .with_context(lang="en_US")
                .search([("name", "=", user.partner_id.name)])
            )
            partner_name = user.partner_id.name

            if user.partner_id and user.partner_id.parent_id:
                partner_name = user.partner_id.parent_id.name + ", " + partner_name

            analytics_obj = self.env["account.analytic.account"].with_context(
                lang="en_US"
            )
            acc_ids = analytics_obj.search([("name", "=", partner_name)])
            if not acc_ids and users:
                partner_tag = self.env.ref("crm_compassion.tag_partners")
                analytics_obj.create(
                    {
                        "name": partner_name,
                        "tag_ids": [(4, partner_tag.id)],
                    }
                )

        return res
