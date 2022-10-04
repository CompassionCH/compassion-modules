##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime
from odoo import api, models


class CompassionHold(models.Model):
    """Send Communication when Hold Removal is received."""

    _inherit = "compassion.hold"

    @api.model
    def beneficiary_hold_removal(self, commkit_data):
        ids = super().beneficiary_hold_removal(commkit_data)
        communication_type = self.env.ref(
            "partner_communication_compassion.lifecycle_child_unplanned_exit"
        )
        if communication_type.active:
            now = datetime.now()
            # when unexpected exit of already assigned child
            # CO-3692 : if the hold was already expired and we wrongly receive
            # another message from GMC child state won't be R (released)
            for hold in self.browse(ids).filtered(
                lambda h: h.expiration_date > now
                and h.child_id.sponsorship_ids
                and h.child_id.state == "R"
            ):
                sponsorship = hold.child_id.sponsorship_ids[:1]
                sponsorship.send_communication(communication_type, both=True)
        return ids
