##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from urllib.parse import urlencode
from urllib.parse import urljoin
from odoo import api, models, fields


class DisasterAlert(models.Model):
    """Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """

    _inherit = "fo.disaster.alert"

    access_link = fields.Char(compute="_compute_access_link")

    def _compute_access_link(self):
        """Generate URL for disaster alert."""
        for disaster in self:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            query = {"db": self.env.cr.dbname}
            fragment = {
                "id": disaster.id,
                "menu_id": self.env.ref(
                    "child_compassion.menu_sponsorship_field_office_disaster_alert"
                ).id,
                "action": self.env.ref(
                    "child_compassion.open_view_field_office_disaster"
                ).id,
            }
            action = "/web?%s#%s" % (urlencode(query), urlencode(fragment))
            disaster.access_link = urljoin(base_url, action)


class ChildImpact(models.Model):
    _inherit = "child.disaster.impact"

    communication_id = fields.Many2one(
        "partner.communication.job", "Communication", readonly=False
    )
    state = fields.Selection(related="communication_id.state")

    @api.model
    def create(self, vals):
        impact = super().create(vals)
        partner = impact.child_id.sponsor_id
        if partner:
            communication_config = self.env.ref(
                "partner_communication_compassion.disaster_alert"
            )
            if communication_config.active:
                sponsorships = partner.sponsorship_ids.filtered(
                    lambda s: s.child_id == impact.child_id
                )
                comm = self.env["partner.communication.job"].create(
                    {
                        "partner_id": partner.id,
                        "config_id": communication_config.id,
                        "object_ids": sponsorships.ids,
                        "user_id": communication_config.user_id.id,
                    }
                )
                impact.communication_id = comm
        return impact
