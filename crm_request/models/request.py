# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from email.utils import parseaddr
from dateutil import parser
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, exceptions, _
from odoo.tools import html_sanitize

_logger = logging.getLogger(__name__)


class CrmClaim(models.Model):
    _inherit = "crm.claim"
    _description = "Request"

    date = fields.Datetime(string="Date", readonly=True, index=False)
    name = fields.Char(compute="_compute_name", store=True)
    subject = fields.Char()
    alias_id = fields.Many2one(
        "mail.alias",
        "Alias",
        help="The destination email address that the contacts used.",
        readonly=False,
    )
    code = fields.Char(string="Number")
    user_id = fields.Many2one(string="Assign to", readonly=False)
    stage_id = fields.Many2one(group_expand="_read_group_stage_ids", readonly=False)
    ref = fields.Char(related="partner_id.ref")
    color = fields.Integer("Color index", compute="_compute_color")
    email_origin = fields.Char()
    language = fields.Selection("_get_lang")
    holiday_closure_id = fields.Many2one(
        "holiday.closure", "Holiday closure", readonly=True
    )

    @api.depends("subject")
    def _compute_name(self):
        for rd in self:
            rd.name = f"{rd.code} - {rd.subject}"

    def _compute_color(self):
        for request in self:
            request.color = 0
            if int(request.priority) == 2:
                request.color = 2

    @api.model
    def _get_lang(self):
        langs = self.env["res.lang"].search([])
        return [(l.code, l.name) for l in langs]

    
    def action_reply(self):
        """
        This function opens a window to compose an email, with the default
        template message loaded by default
        """
        self.ensure_one()
        original_partner = self.partner_id

        if not original_partner:
            raise exceptions.UserError(_("You can only reply if you set the partner."))

        if not self.language:
            raise exceptions.UserError(_("Language must be specified."))

        template_id = self.categ_id.template_id.id
        ctx = {
            "default_model": "crm.claim",
            "default_res_id": self.id,
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment",
            "mark_so_as_sent": True,
            "salutation_language": self.language,
        }

        if original_partner:
            alias_partner = self._get_partner_alias(
                original_partner, parseaddr(self.email_from)[1]
            )
            if alias_partner == original_partner:
                partner = original_partner
            else:
                partner = alias_partner
            ctx["default_partner_ids"] = [partner.id]

            messages = self.mapped("message_ids").filtered(
                lambda m: m.body
                and (m.author_id == partner or partner in m.partner_ids)
            )
            if messages:
                # Put quote of previous message in context for using in
                # mail compose message wizard
                message = messages.filtered(lambda m: m.author_id == partner)[:1]
                if message:
                    ctx["reply_quote"] = message.get_message_quote()
                    ctx["message_id"] = message.id

            # Un-archive the email_alias so that a mail can be sent and set a
            # flag to re-archive them once the email is sent.
            if partner.contact_type == "attached" and not partner.active:
                partner.toggle_active()
        else:
            ctx["claim_no_partner"] = True

        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "target": "new",
            "context": ctx,
        }

    def _get_partner_alias(self, partner, email):
        if email and partner.email.lower() != email.lower():
            for partner_alias in partner.other_contact_ids:
                if partner_alias.email.lower() == email.lower():
                    return partner_alias
            # No match is found
            raise exceptions.Warning(_("No partner aliases match: %s !") % email)
        else:
            return partner

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """Unlink the email_from field from the partner"""
        if self.partner_id:
            self.partner_phone = self.partner_id.phone

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = stages._search([("active", "=", True)], order=order)
        return stages.browse(stage_ids)

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------
    @api.model
    def message_new(self, msg, custom_values=None):
        """Use the html of the mail's body instead of html converted in text"""
        msg["body"] = html_sanitize(msg.get("body", ""))

        if custom_values is None:
            custom_values = {}

        alias_char = parseaddr(msg.get("to"))[1].split("@")[0]
        alias = self.env["mail.alias"].search([["alias_name", "=", alias_char]])

        # Find the corresponding type
        subject = msg.get("subject", "")
        category_ids = self.env["crm.claim.category"].search(
            [("keywords", "!=", False)]
        )
        category_id = False
        for record in category_ids:
            if any(word in subject for word in record.get_keys()):
                category_id = record.id
                break

        defaults = {
            "date": msg.get("date"),  # Get the time of the sending of the mail
            "alias_id": alias.id,
            "categ_id": category_id,
            "subject": subject,
            "email_origin": msg.get("from"),
        }

        # If the mail is ignored_reporters use the email in the body instead
        ignored_reporter = self.env["ignored.reporter"].search([]).mapped("email")
        if defaults["email_origin"] in ignored_reporter:
            email = msg["reply_to"]
            defaults["email_origin"] = email
            msg["from"] = email
            msg["email_from"] = email

        if "partner_id" not in custom_values:
            match_obj = self.env["res.partner.match"]
            options = {"skip_create": True}
            partner = match_obj.match_partner_to_infos(
                {"email": parseaddr(defaults["email_origin"])[1]}, options
            )
            if partner:
                defaults["partner_id"] = partner.id
                defaults["language"] = partner.lang

        # Check here if the date of the mail is during a holiday
        mail_date = msg.get("date")
        defaults["holiday_closure_id"] = (
            self.env["holiday.closure"]
            .search(
                [("start_date", "<=", mail_date), ("end_date", ">=", mail_date)],
                limit=1,
            )
            .id
        )

        defaults.pop("name", False)
        defaults.update(custom_values)

        request_id = super().message_new(msg, defaults)
        request = self.browse(request_id.id)
        if not request.language:
            request.language = (
                self.env["langdetect"].detect_language(request.description).lang_id.code
            )

        # # send automated holiday response
        try:
            if request.holiday_closure_id:
                request.send_holiday_answer()
        except Exception as e:
            _logger.error(f"The automatic mail failed\n{e}")

        return request_id

    
    def message_update(self, msg_dict, update_vals=None):
        """Change the stage to "Waiting on support" when the customer write a
        new mail on the thread
        """
        result = super().message_update(msg_dict, update_vals)
        msg_date = parser.parse(msg_dict["date"])
        for request in self:
            request.stage_id = self.env["ir.model.data"].get_object_reference(
                "crm_request", "stage_wait_support"
            )[1]

            if (
                request.user_id
                and self.env["hr.leave"].search(
                    [
                        ("employee_id", "in", request.user_id.employee_ids.ids),
                        ("date_from", "<=", msg_date),
                        ("date_to", ">=", msg_date),
                        "|",
                        ("state", "=", "validate"),
                        ("state", "=", "confirm"),
                    ],
                    count=True,
                )
                != 0
            ):
                request.stage_id = self.env["ir.model.data"].get_object_reference(
                    "crm_claim", "stage_claim1"
                )[1]
                request.user_id = False
        return result

    
    urns("self", lambda value: value.id)
    def message_post(self, **kwargs):
        """Change the stage to "Resolve" when the employee answer
        to the supporter but not if it's an automatic answer.
        """
        result = super().message_post(**kwargs)

        if "mail_server_id" in kwargs and not self.env.context.get("keep_stage"):
            for request in self:
                ir_data = self.env["ir.model.data"]
                request.stage_id = ir_data.get_object_reference(
                    "crm_claim", "stage_claim2"
                )[1]

        return result

    
    def create(self, values):
        ignored_reporter = self.env["ignored.reporter"].search([]).mapped("email")
        if values.get("partner_id"):
            partner_id = values.get("partner_id")
            partner = self.env["res.partner"].browse(partner_id)
            partner = self.get_partner_parent(partner)
            if partner.email in ignored_reporter:
                del values["partner_id"]
            else:
                values["partner_id"] = partner.id
        return super().create(values)

    @staticmethod
    def get_partner_parent(partner):
        """
        if the mail used refer to an alternative partner identity
        iteratively take the partner 'parent' instead
        here we use a for loop with 10 steps to avoid an infinite while
        which can occur for example with circular references
        """
        for _ in range(10):
            if not partner.contact_id:
                break
            partner = partner.contact_id
        return partner

    
    def write(self, values):
        """
        - If a user is assigned and the request is 'New', set to 'Waiting on support'
        - If move request in stage 'Waiting on support' assign the request to
        the current user.
        - Push partner to associated mail messages
        """
        if values.get("user_id") and self.stage_id == self.env.ref(
            "crm_claim.stage_claim1"
        ):
            values["stage_id"] = self.env.ref("crm_request.stage_wait_support").id

        if not values.get("user_id") and values.get("stage_id") in (
            self.env.ref("crm_request.stage_wait_support").id,
            self.env.ref("crm_claim.stage_claim2").id,
        ):
            for request in self:
                if not request.user_id:
                    values["user_id"] = self.env.uid

        super().write(values)

        if values.get("partner_id"):
            for request in self:
                request.message_ids.filtered(
                    lambda m: m.email_from == request.email_origin
                ).write({"author_id": values["partner_id"]})
        return True

    
    def send_holiday_answer(self):
        """This will use the holiday mail template and enforce a
        mail sending to the requester."""
        template = self.env.ref("crm_request.business_closed_email_template")
        for request in self:
            template.with_context(lang=request.language).send_mail(
                request.id,
                force_send=True,
                email_values={"email_to": request.email_origin},
            )

    @api.model
    def cron_reminder_request(self):
        """Periodically sends a reminder to unaddressed request (new, waiting for support)"""

        new_stage_id = self.env.ref("crm_claim.stage_claim1").id
        wait_support_stage_id = self.env.ref("crm_request.stage_wait_support").id

        request_to_notify = self.search(
            [
                ("stage_id", "in", [new_stage_id, wait_support_stage_id]),
                ("user_id", "!=", False),
                ("user_id", "not in", [187]),  # Exclude Sarah
                ("write_date", "<", fields.datetime.now() - relativedelta(weeks=1)),
            ]
        )

        for req in request_to_notify:
            req.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("A support request require your attention"),
                note=_(
                    "The request {} you were assigned to requires"
                    " your attention.".format(req.code)
                ),
                user_id=req.user_id.id,
            )
