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
from datetime import datetime, timedelta
from enum import Enum
from functools import reduce

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class HoldType(Enum):
    """Defines available Hold Types."""

    CHANGE_COMMITMENT_HOLD = "Change Commitment Hold"
    CONSIGNMENT_HOLD = "Consignment Hold"
    DELINQUENT_HOLD = "Delinquent Mass Cancel Hold"
    E_COMMERCE_HOLD = "E-Commerce Hold"
    NO_MONEY_HOLD = "No Money Hold"
    REINSTATEMENT_HOLD = "Reinstatement Hold"
    RESERVATION_HOLD = "Reservation Hold"
    SPONSOR_CANCEL_HOLD = "Sponsor Cancel Hold"
    SUB_CHILD_HOLD = "Sub Child Hold"

    @staticmethod
    def get_hold_types():
        return [attr.value for attr in HoldType]

    @staticmethod
    def from_string(hold_type):
        """Gets the HoldType given its string representation."""
        for etype in HoldType:
            if etype.value == hold_type:
                return etype
        return False


class AbstractHold(models.AbstractModel):
    """Defines the basics of each model that must set up hold values."""

    _name = "compassion.abstract.hold"
    _description = "Compassion Abstract Hold"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    type = fields.Selection(
        "get_hold_types", required=True, default=HoldType.CONSIGNMENT_HOLD.value
    )
    expiration_date = fields.Datetime(required=True)
    primary_owner = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        domain=[("share", "=", False)],
        readonly=False,
    )
    secondary_owner = fields.Char()
    ambassador = fields.Many2one("res.partner", readonly=False)
    yield_rate = fields.Integer()
    no_money_yield_rate = fields.Integer()
    channel = fields.Selection(
        [
            ("web", "Website"),
            ("event", "Event"),
            ("ambassador", "Ambassador"),
            ("sponsor_cancel", "Sponsor Cancel"),
            ("sub", "SUB Sponsorship"),
        ]
    )
    source_code = fields.Char()
    comments = fields.Char()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def get_hold_types(self):
        return [(hold, hold) for hold in HoldType.get_hold_types()]

    @api.model
    def get_default_hold_expiration(self, hold_type):
        """
        Get the default hold expiration date.
        :param hold_type: HoldType Enum
        :return:
        """
        config_obj = self.env["res.config.settings"]
        hold_param = hold_type.name.lower() + "_duration"
        duration = config_obj.sudo().get_param(hold_param, 15)
        diff = (
            timedelta(days=duration)
            if hold_type != HoldType.E_COMMERCE_HOLD
            else timedelta(minutes=duration)
        )
        return fields.Datetime.to_string(datetime.now() + diff)

    @api.onchange("type")
    def onchange_type(self):
        default_hold = self.env.context.get("default_expiration_date")
        self.expiration_date = default_hold or self.get_default_hold_expiration(
            HoldType.from_string(self.type)
        )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_fields(self):
        """Returns the fields for which we want to know the value."""
        return [
            "type",
            "expiration_date",
            "primary_owner",
            "secondary_owner",
            "yield_rate",
            "no_money_yield_rate",
            "channel",
            "source_code",
            "comments",
            "ambassador",
        ]

    def get_hold_values(self):
        """Get the field values of one record.
        :return: Dictionary of values for the fields
        """
        self.ensure_one()
        vals = self.read(self.get_fields())[0]
        vals["primary_owner"] = vals["primary_owner"][0]
        ambassador = vals.get("ambassador")
        if ambassador:
            vals["ambassador"] = ambassador[0]
        del vals["id"]
        return vals


class CompassionHold(models.Model):
    _name = "compassion.hold"
    _rec_name = "hold_id"
    _inherit = [
        "compassion.abstract.hold",
        "mail.thread",
        "mail.activity.mixin",
        "compassion.mapped.model",
    ]
    _description = "Compassion hold"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    hold_id = fields.Char(readonly=True, tracking=True)
    child_id = fields.Many2one("compassion.child", "Child on hold", readonly=True)
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("expired", "Expired")],
        readonly=True,
        default="draft",
        tracking=True,
        index=True,
    )
    reinstatement_reason = fields.Char(readonly=True)
    reservation_id = fields.Many2one(
        "compassion.reservation", "Reservation", readonly=False
    )
    no_money_extension = fields.Integer(
        help="Counts how many time the no money hold was extended."
    )

    # Track field changes
    ambassador = fields.Many2one(tracking=True, readonly=False)
    primary_owner = fields.Many2one(tracking=True, readonly=False)
    type = fields.Selection(tracking=True, index=True)
    channel = fields.Selection(tracking=True)
    expiration_date = fields.Datetime(
        tracking=True,
        required=False,
        default=datetime.now() + timedelta(days=60),
        index=True,
    )

    _sql_constraints = [
        ("hold_id", "unique(hold_id)", "The hold already exists in database."),
    ]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        # Avoid duplicating Holds
        hold_id = vals.get("hold_id")
        if hold_id:
            hold = self.search([("hold_id", "=", hold_id)])
            if hold:
                hold.write(vals)
                return hold
        return super().create(vals)

    def write(self, vals):
        if "expiration_date" in vals and self.filtered(
            lambda h: h.expiration_date < datetime.now()
        ):
            raise UserError(_("Sorry, the child is no longer available."))

        res = super().write(vals)
        notify_vals = ["primary_owner", "type", "expiration_date"]
        notify = reduce(lambda prev, val: prev or val in vals, notify_vals, False)
        if notify and not self.env.context.get("no_upsert"):
            self.update_hold()

        return res

    def unlink(self):
        """
        Don't unlink active holds, but only those that don't relate to
        a child anymore (child released).
        :return: True
        """
        active_holds = self.filtered(
            lambda h: h.state == "active" and h.expiration_date > datetime.now()
        )
        active_holds.release_hold()
        inactive_holds = self - active_holds
        super(CompassionHold, inactive_holds).unlink()
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def update_hold(self):
        message_obj = self.env["gmc.message"].with_context(async_mode=False)
        action_id = self.env.ref("child_compassion.create_hold").id
        messages = message_obj
        for hold in self:
            message_vals = {
                "action_id": action_id,
                "object_id": hold.id,
                "child_id": hold.child_id.id,
            }
            messages += message_obj.create(message_vals)
        messages.process_messages()
        failed = messages.filtered(lambda m: "failure" in m.state)
        if failed:
            raise UserError("\n\n".join(failed.mapped("failure_reason")))

    def hold_sent(self, vals):
        """Called when hold is sent to Connect."""
        self.write(vals)
        # update compassion children with hold_id received
        for hold in self:
            child_to_update = hold.child_id
            if hold.hold_id:
                hold.state = "active"
                old_hold = child_to_update.hold_id
                if not old_hold:
                    child_to_update.child_consigned(hold.id)
                elif (
                    old_hold.hold_id != hold.hold_id
                    and old_hold.expiration_date < datetime.now()
                ):
                    child_to_update.hold_id = hold
                    old_hold.unlink()
            else:
                # Release child if no hold_id received
                hold.unlink()
                child_to_update.child_released()

    @api.model
    def reinstatement_notification(self, commkit_data):
        """Called when a child was Reinstated."""
        # Reinstatement holds are available for 90 days (Connect default)
        in_90_days = datetime.now() + timedelta(days=90)

        hold_data = commkit_data.get("ReinstatementHoldNotification", commkit_data)
        vals = self.json_to_data(hold_data)
        child_id = vals.get("child_id")
        if not child_id:
            raise ValueError("No child found")
        child = self.env["compassion.child"].browse(child_id)
        if child.state not in ("F", "R"):
            raise UserError(_("Child is not departed."))
        vals.update(
            {
                "expiration_date": in_90_days,
                "state": "active",
                "comments": "Child was reinstated! Be sure to propose it to its "
                "previous sponsor.",
            }
        )
        hold = self.create(vals)
        child.child_consigned(hold.id)

        # Update hold duration to what is configured
        hold.write(
            {
                "expiration_date": self.get_default_hold_expiration(
                    HoldType.REINSTATEMENT_HOLD
                )
            }
        )

        child.get_lifecycle_event()

        return [hold.id]

    def reservation_to_hold(self, commkit_data):
        """Called when a reservation gots converted to a hold."""
        hold_data = commkit_data.get("ReservationConvertedToHoldNotification")
        child_global_id = hold_data and hold_data.get("Beneficiary_GlobalID")
        if child_global_id:
            child = self.env["compassion.child"].create({"global_id": child_global_id})
            hold = self.env["compassion.hold"].create(self.json_to_data(hold_data))
            hold.write(
                {
                    "state": "active",
                    "ambassador": hold.reservation_id.ambassador.id,
                    "channel": hold.reservation_id.channel,
                }
            )
            child.child_consigned(hold.id)
            reservation = hold.reservation_id
            reservation_state = "active"
            number_reserved = reservation.number_reserved + 1
            if (
                number_reserved == reservation.number_of_beneficiaries
                or reservation.reservation_type == "child"
            ):
                reservation_state = "expired"
            reservation.write(
                {"state": reservation_state, "number_reserved": number_reserved}
            )

            # Notify reservation owner
            hold.sudo().message_post(
                body=_(
                    "A new hold has been created because of an existing reservation."
                ),
                subject=_("%s - Reservation converted to hold") % child.local_id,
                partner_ids=hold.primary_owner.partner_id.ids,
                subtype_xmlid="mail.mt_comment",
                content_subtype="plaintext",
            )

            return [hold.id]

        return list()

    def button_release_hold(self):
        """
        Prevent releasing No Money Holds!
        """
        if self.filtered(lambda h: h.type == HoldType.NO_MONEY_HOLD.value):
            raise UserError(_("You cannot release No Money Hold!"))
        return self.release_hold()

    def release_hold(self):
        messages = self.env["gmc.message"].with_context(async_mode=False)
        action_id = self.env.ref("child_compassion.release_hold").id

        for hold in self:
            messages += messages.create({"action_id": action_id, "object_id": hold.id})
        try:
            messages.process_messages()
            self.hold_released()
        except Exception:
            self.env.clear()
            messages.env.clear()
            logger.error("Some holds couldn't be released.")
            messages.write({"state": "failure"})
            # Force hold removal on our side without releasing the child
            self.write({"state": "expired"})
            self.mapped("child_id").write({"hold_id": False})
        return True

    def hold_released(self, vals=None):
        """Called when release message was successfully sent to GMC."""
        self.write({"state": "expired"})
        self.mapped("child_id").child_released()
        return True

    @api.model
    def check_hold_validity(self):
        """
        Remove expired holds
        :return: True
        """
        holds = self.search([("state", "=", "draft")])
        holds.unlink()
        return True

    @api.model
    def postpone_no_money_cron(self):
        # Search for expiring No Money Hold
        this_week_delay = datetime.now() + timedelta(days=7)
        holds = self.search(
            [
                ("state", "=", "active"),
                ("expiration_date", "<=", this_week_delay),
                (
                    "type",
                    "in",
                    [HoldType.NO_MONEY_HOLD.value, HoldType.SUB_CHILD_HOLD.value],
                ),
            ]
        )
        holds.postpone_no_money_hold()
        return True

    @api.model
    def beneficiary_hold_removal(self, commkit_data):
        data = commkit_data.get("BeneficiaryHoldRemovalNotification")
        hold = self.search([("hold_id", "=", data.get("HoldID"))])

        # avoid realising a hold (and related child) that has already been released
        if hold and hold.state == "expired":
            logger.warning(
                "Received Participant Hold Removal order from GMC for"
                "already expired hold."
            )
            return hold.ids

        if not hold:
            child = self.env["compassion.child"].search(
                [("global_id", "=", data.get("Beneficiary_GlobalID"))]
            )
            if not child:
                # return -1 is better than an empty list, as it allow us a
                # better error handling
                return [-1]
            hold = child.hold_id
            if not hold:
                hold = self.create(
                    {
                        "hold_id": data.get("HoldID"),
                        "expiration_date": fields.Datetime.now(),
                        "child_id": child.id,
                    }
                )

        hold.comments = data.get("NotificationReason")
        hold.hold_released()
        return [hold.id]

    def postpone_no_money_hold(self, additional_text=None):
        """
        When a No Money Hold is expiring, this will extend the hold duration.
        Only 2 extensions are allowed, then the hold is not modified.
        Send a notification to hold owner.
        :return: None
        """
        settings = self.env["res.config.settings"].sudo()
        first_extension = settings.get_param("no_money_hold_duration")
        second_extension = settings.get_param("no_money_hold_extension")

        for hold in self.filtered(lambda h: h.no_money_extension < 3):

            old_date = hold.expiration_date
            hold_extension = (
                first_extension if not hold.no_money_extension else second_extension
            )
            new_hold_date = hold.expiration_date + timedelta(days=hold_extension)
            values = {
                "local_id": hold.child_id.local_id,
                "old_expiration": old_date,
                "new_expiration": new_hold_date.strftime("%d %B %Y"),
                "extension_description": 'first' if not hold.no_money_extension else 'second',
                "additional_text": str(additional_text) if additional_text else "",
            }

            if hold.child_id.sponsor_id: # Check that a sponsorship exists
                next_extension = hold.no_money_extension
                if hold.type == HoldType.NO_MONEY_HOLD.value:
                    next_extension += 1
                hold_vals = {
                    "no_money_extension": next_extension,
                    "expiration_date": new_hold_date,
                }
                hold.write(hold_vals)

                body = (
                    "The no money hold for child {local_id} was expiring on "
                    "{old_expiration} and was extended to {new_expiration} ({extension_description} extension)."
                    "{additional_text}"
                )
                hold.message_post(
                    body=_(body.format(**values)),
                    subject=_("No money hold extension"),
                    subtype_xmlid="mail.mt_comment",
                )

            else:
                body = (
                    "The no money hold for child {local_id} is expiring on "
                    "{old_expiration} and will not be extended since no sponsorship exists for this child."
                )
                hold.message_post(
                    body=_(body.format(**values)),
                )


    ##########################################################################
    #                              Mapping METHOD                            #
    ##########################################################################

    def data_to_json(self, mapping_name=None):
        json_data = super().data_to_json(mapping_name)
        for key, val in json_data.copy().items():
            if not val:
                del json_data[key]
        # Read manually Primary Owner, to avoid security restrictions on
        # companies in case the owner is in another company.
        if len(self) == 1:
            json_data["PrimaryHoldOwner"] = self.primary_owner.sudo().name
        elif self:
            for i, hold in enumerate(self):
                json_data[i]["PrimaryHoldOwner"] = hold.primary_owner.sudo().name
        return json_data
