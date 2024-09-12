from odoo import _, models
from odoo.exceptions import UserError

SPONSORSHIP_STATE_ACTIVE = "active"


class CustomMergePartnerAutomatic(models.TransientModel):
    """
    This model overrides the 'action_merge' method of the
    base.partner.merge.automatic.wizard model to provide custom logic for merging
    partners with active contracts.
    """

    _inherit = "base.partner.merge.automatic.wizard"

    def action_merge(self):
        self._check_sponsorship_contract()
        return super().action_merge()

    def _check_sponsorship_contract(self):
        """
        Check for active contracts related to the selected partners.

        This method searches for active contracts related to the selected partners
        (excluding the destination partner) before proceeding with the merge action.
        If any active contracts are found, it raises a UserError to prevent the merge.
        """
        partner_ids: list[int] = (self.partner_ids - self.dst_partner_id).ids

        active_sponsorship_contracts = self.env["recurring.contract"].search_count(
            [
                "&",
                "|",
                ("partner_id", "in", partner_ids),
                ("correspondent_id", "in", partner_ids),
                ("state", "=", SPONSORSHIP_STATE_ACTIVE),
            ]
        )

        if active_sponsorship_contracts:  # Check if any active contracts are found
            error_message = _("Cannot merge partners because active contracts exist.")
            raise UserError(error_message)
