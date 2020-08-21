##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import api, models, fields

logger = logging.getLogger(__name__)


class Phonecall(models.Model):
    """ Add a communication when phonecall is logged. """

    _inherit = "crm.phonecall"

    communication_id = fields.Many2one(
        "partner.communication.job", "Communication", readonly=False
    )

    @api.model
    def create(self, vals_list):
        phonecalls = super().create(vals_list)
        for phonecall in phonecalls:
            if phonecall.communication_id and phonecall.state == "done":
                # Link phonecall to communication when log created from
                # communication call wizard.
                communication = phonecall.communication_id
                communication.phonecall_id = phonecall
            else:
                phonecall.log_partner_communication()
        return phonecalls

    def write(self, values):
        super().write(values)
        if values.get("state") == "done":
            self.log_partner_communication()
        return True

    def log_partner_communication(self):
        config = self.env.ref("partner_communication.phonecall_communication")
        for phonecall in self:
            if phonecall.state == "done" and phonecall.partner_id \
                    and not phonecall.communication_id:
                # Phone call was made outside from communication call wizard.
                # Create a communication to log the call.
                phonecall.communication_id = \
                    self.env["partner.communication.job"].create({
                        "config_id": config.id,
                        "partner_id": phonecall.partner_id.id,
                        "user_id": self.env.uid,
                        "object_ids": phonecall.partner_id.ids,
                        "state": "done",
                        "phonecall_id": phonecall.id,
                        "sent_date": phonecall.date or fields.Datetime.now(),
                        "body_html": phonecall.name,
                        "subject": phonecall.name,
                        "auto_send": False,
                    })
        return True
