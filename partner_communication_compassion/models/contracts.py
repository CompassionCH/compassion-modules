##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _

logger = logging.getLogger(__name__)


class RecurringContract(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """

    _inherit = ["recurring.contract", "translatable.model"]
    _name = "recurring.contract"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    send_introduction_letter = fields.Boolean(
        string="Send B2S intro letter to sponsor", default=True
    )
    new_picture = fields.Boolean(
        help="Indicates a new picture was received and not yet transmitted to the sponsor."
    )

    @api.onchange("origin_id")
    def _do_not_send_letter_to_transfer(self):
        if self.origin_id.type == "transfer" or self.origin_id.name == "Reinstatement":
            self.send_introduction_letter = False
        # If origin is switched back from a transer,
        # field should be reset to default
        else:
            self.send_introduction_letter = True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def send_communication(self, communication, correspondent=True, both=False):
        """
        Sends a communication to selected sponsorships.
        :param communication: the communication config to use
        :param correspondent: put to false for sending to payer instead of
                              correspondent.
        :param both:          send to both correspondent and payer
                              (overrides the previous parameter)
        :return: communication created recordset
        """
        partner_field = "correspondent_id" if correspondent else "partner_id"
        partners = self.mapped(partner_field)
        communications = self.env["partner.communication.job"]
        if not communication.active:
            return communications
        if both:
            for contract in self:
                communications += self.env["partner.communication.job"].create(
                    {
                        "config_id": communication.id,
                        "partner_id": contract.partner_id.id,
                        "object_ids": self.env.context.get(
                            "default_object_ids", contract.id
                        ),
                    }
                )
                if contract.correspondent_id != contract.partner_id:
                    communications += self.env["partner.communication.job"].create(
                        {
                            "config_id": communication.id,
                            "partner_id": contract.correspondent_id.id,
                            "object_ids": self.env.context.get(
                                "default_object_ids", contract.id
                            ),
                        }
                    )
        else:
            for partner in partners:
                objects = self.filtered(
                    lambda c: c.correspondent_id == partner
                    if correspondent
                    else c.partner_id == partner
                )
                communications += self.env["partner.communication.job"].create(
                    {
                        "config_id": communication.id,
                        "partner_id": partner.id,
                        "object_ids": self.env.context.get(
                            "default_object_ids", objects.ids
                        ),
                    }
                )
        return communications

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    def _contract_cancelled(self, optional_vals):
        # Remove pending communications
        for contract in self:
            self.env["partner.communication.job"].search(
                [
                    ("config_id.model_id.model", "=", self._name),
                    "|",
                    ("partner_id", "=", contract.partner_id.id),
                    ("partner_id", "=", contract.correspondent_id.id),
                    ("object_ids", "like", contract.id),
                    ("state", "=", "pending"),
                ]
            ).unlink()
        return super()._contract_cancelled(optional_vals)

    def action_cancel_draft(self):
        """Cancel communication"""
        super().action_cancel_draft()
        cancel_config = self.env.ref(
            "partner_communication_compassion.sponsorship_cancellation"
        )
        for contract in self:
            self.env["partner.communication.job"].search(
                [
                    ("config_id", "=", cancel_config.id),
                    "|",
                    ("partner_id", "=", contract.partner_id.id),
                    ("partner_id", "=", contract.correspondent_id.id),
                    ("object_ids", "like", contract.id),
                    ("state", "=", "pending"),
                ]
            ).unlink()
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _on_sponsorship_finished(self):
        super()._on_sponsorship_finished()
        cancellation = self.env.ref(
            "partner_communication_compassion.sponsorship_cancellation"
        )
        depart = self.env.ref("sponsorship_compassion.end_reason_depart")

        # prevent normal communication on unexpected hold end. in this particular case
        # a special communication will be send.
        s_to_notify = self.filtered(lambda s: not s._is_unexpected_end())

        # Send cancellation for regular sponsorships
        s_to_notify.filtered(
            lambda s: s.end_reason_id != depart and not s.parent_id
        ).with_context({}).send_communication(cancellation, both=True)
        # Send NO SUB letter if activation is less than two weeks ago
        # otherwise send Cancellation letter for SUB sponsorships
        activation_limit = date.today() - relativedelta(days=15)
        s_to_notify.filtered(
            lambda s: s.end_reason_id != depart
            and s.parent_id
            and (
                s.activation_date
                and fields.Date.from_string(s.activation_date) < activation_limit
            )
        ).with_context({}).send_communication(cancellation, both=True)

    def _is_unexpected_end(self):
        """Check if sponsorship hold had an unexpected end or not."""
        self.ensure_one()

        # subreject could happened before hold expiration and should not be considered
        # as unexpected
        subreject = self.env.ref("sponsorship_compassion.end_reason_subreject")

        if self.end_reason_id == subreject:
            return False

        return self.hold_id and not datetime.now() > self.hold_id.expiration_date
