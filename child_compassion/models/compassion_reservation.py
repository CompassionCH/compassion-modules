##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import datetime
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CompassionReservation(models.Model):
    _name = "compassion.reservation"
    _description = "Project Reservation"
    _inherit = ["compassion.abstract.hold", "mail.thread", "compassion.mapped.model"]
    _rec_name = "reservation_id"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    reservation_id = fields.Char(readonly=True)
    reservation_type = fields.Selection(
        [("project", "Project reservation"), ("child", "Child reservation")],
        required=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("expired", "Expired")],
        readonly=True,
        default="draft",
        track_visibility="onchange",
    )
    fcp_id = fields.Many2one(
        "compassion.project", "Project", oldname="icp_id", readonly=False
    )
    child_id = fields.Many2one(
        "compassion.child",
        "Child",
        domain=[("global_id", "!=", False), ("hold_id", "=", False)],
        readonly=False,
    )
    child_global_id = fields.Char(
        compute="_compute_child_global_id",
        inverse="_inverse_child_global_id",
        store=True,
    )
    campaign_event_identifier = fields.Char()
    expiration_date = fields.Datetime(
        "Hold expiration date", track_visibility="onchange"
    )
    reservation_expiration_date = fields.Date(
        required=True,
        track_visibility="onchange",
        default=lambda s: s._default_expiration_date(),
    )
    is_reservation_auto_approved = fields.Boolean(default=True)
    number_of_beneficiaries = fields.Integer(track_visibility="onchange")
    number_reserved = fields.Integer()

    _sql_constraints = [
        (
            "reservation_id",
            "unique(reservation_id)",
            "The Reservation already exists in database.",
        ),
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends("child_id")
    def _compute_child_global_id(self):
        for reservation in self.filtered("child_id"):
            reservation.child_global_id = reservation.child_id.global_id

    @api.multi
    def _inverse_child_global_id(self):
        for reservation in self.filtered("child_global_id"):
            child = self.env["compassion.child"].search(
                [("global_id", "=", reservation.child_global_id)]
            )
            if not child:
                # Create child (not available yet to us)
                child = self.env["compassion.child"].create(
                    {"global_id": reservation.child_global_id, }
                )
            reservation.child_id = child

    def _default_expiration_date(self):
        days_reservation = (
            self.env["res.config.settings"].sudo().get_param("reservation_duration")
        )
        dt = timedelta(days=days_reservation)
        expiration = datetime.date.today() + dt
        return expiration

    ##########################################################################
    #                             ORM METHODS                                #
    ##########################################################################
    @api.multi
    def write(self, vals):
        res = super().write(vals)
        sync_fields = [
            "reservation_expiration_date",
            "expiration_date",
            "number_of_beneficiaries",
            "primary_owner",
        ]
        sync = False
        for field in sync_fields:
            if field in vals:
                sync = True
                break
        if sync:
            messages = (
                self.with_context(async_mode=False)
                    .filtered(lambda r: r.state == "active")
                    .handle_reservation()
            )
            failed = messages.filtered(lambda m: m.state == "failure")
            if failed:
                raise UserError("\n\n".join(failed.mapped("failure_reason")))
        return res

    @api.multi
    def unlink(self):
        active = self.filtered(lambda r: r.state == "active")
        draft = self.filtered(lambda r: r.state == "draft")
        active.cancel_reservation()
        super(CompassionReservation, draft).unlink()
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def check_reservation_validity(self):
        expired_reservations = self.env["compassion.reservation"].search(
            [("expiration_date", "<", fields.Datetime.now())]
        )
        expired_reservations.write({"state": "expired"})
        return True

    def handle_reservation(self, cancel=False):
        messages = self.env["gmc.message"]
        action = False
        for reservation in self:
            if reservation.reservation_type == "child":
                if cancel:
                    action = self.env.ref("child_compassion.cancel_reservation_child")
                else:
                    action = self.env.ref("child_compassion.beneficiary_reservation")
            elif reservation.reservation_type == "project":
                if cancel:
                    action = self.env.ref("child_compassion.cancel_reservation")
                else:
                    action = self.env.ref("child_compassion.create_reservation")
            messages += messages.create(
                {
                    "action_id": action.id,
                    "object_id": reservation.id,
                    "child_id": reservation.child_id.id,
                }
            )

        messages.process_messages()
        return messages

    def reservation_create_answer(self, vals):
        """ Called when receiving the answer of CreateReservation message. """
        vals["state"] = "active"
        return self.write(vals)

    def reservation_create_answer_fail(self, vals):
        """ Called when the reservation has failed"""
        self.message_post(
            subject=_("Reservation failed"),
            body=_("[" + str(vals["Code"]) + "] " + vals["Message"]),
            message_type="comment",
        )

    def reservation_cancel_answer(self, vals):
        """ Called when receiving the answer of CreateReservation message. """
        vals["state"] = "expired"
        return self.write(vals)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def send_reservation(self):
        return self.with_context(async_mode=False).handle_reservation()

    @api.multi
    def cancel_reservation(self):
        self.with_context(async_mode=False).handle_reservation(cancel=True)
        return True

    @api.multi
    def show_reserved_children(self):
        self.ensure_one()

        holds = self.env["compassion.hold"].search([("reservation_id", "=", self.id)])
        children_ids = holds.mapped("child_id.id")

        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "res_model": "compassion.child",
            "domain": [("id", "in", children_ids)],
            "view_mode": "tree,form",
            "target": "current",
        }

    @api.onchange("reservation_expiration_date")
    def onchange_expiration_date(self):
        if not self.reservation_expiration_date:
            return
        expiration = self.reservation_expiration_date
        days_on_hold = (
            self.env["res.config.settings"]
                .sudo()
                .get_param("reservation_hold_duration")
        )
        dt = timedelta(days=days_on_hold)
        self.expiration_date = fields.Datetime.to_datetime(expiration + dt)

    ##########################################################################
    #                              Mapping METHOD                            #
    ##########################################################################
    @api.multi
    def data_to_json(self, mapping_name=None):
        json_data = super().data_to_json(mapping_name)
        # Read manually Primary Owner, to avoid security restrictions on
        # companies in case the owner is in another company.
        if len(self) == 1:
            json_data["PrimaryOwner"] = self.primary_owner.sudo().name
        elif self:
            for i, reservation in enumerate(self):
                json_data[i]["PrimaryOwner"] = reservation.primary_owner.sudo().name
        return json_data
