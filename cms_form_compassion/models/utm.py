from odoo import models, _


class UtmMixin(models.AbstractModel):
    _inherit = "utm.mixin"

    def get_utms(self, utm_source=False, utm_medium=False, utm_campaign=False):
        """
        Finds the utm records given their name
        :param utm_source:
        :param utm_medium:
        :param utm_campaign:
        :return: dictionary with utm ids
        """
        utm_source_id = False
        if utm_source:
            utm_source_id = (
                self.env["utm.source"].search([("name", "=", utm_source)], limit=1).id
            )
        utm_medium_id = False
        if utm_medium:
            utm_medium_id = (
                self.env["utm.medium"].search([("name", "=", utm_medium)],
                                              limit=1).id
                or utm_medium_id
            )
        utm_campaign_id = False
        if utm_campaign:
            utm_campaign_id = (
                self.env["utm.campaign"]
                    .search([("name", "=", utm_campaign)], limit=1)
                    .id
            )
        return {
            "source": utm_source_id,
            "medium": utm_medium_id,
            "campaign": utm_campaign_id,
        }
