# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from email.utils import parseaddr

from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import email_normalize, html_sanitize, prepend_html_content

_logger = logging.getLogger(__name__)


class CrmClaim(models.Model):
    _inherit = "crm.claim"
    _description = "Request"

    date = fields.Datetime(string="Date", readonly=True, index=False)
    alias_id = fields.Many2one(
        "mail.alias",
        "Alias",
        help="The destination email address that the contacts used.",
        readonly=False,
    )
    user_id = fields.Many2one(string="Assign to", readonly=False)
    stage_id = fields.Many2one(group_expand="_read_group_stage_ids", readonly=False)
    ref = fields.Char(related="partner_id.ref")
    color = fields.Integer("Color index", compute="_compute_color")
    language = fields.Selection("_get_lang")
    holiday_closure_id = fields.Many2one(
        "holiday.closure", "Holiday closure", readonly=True
    )
    incoming_message_id = fields.Many2one(
        "mail.message", compute="_compute_incoming_message"
    )
    incoming_message = fields.Html(compute="_compute_incoming_message")
    quoted_reply = fields.Html(compute="_compute_incoming_message")
    reply_to = fields.Char(compute="_compute_incoming_message")

    def _compute_color(self):
        for request in self:
            request.color = 0
            if int(request.priority) == 2:
                request.color = 2

    @api.model
    def _get_lang(self):
        langs = self.env["res.lang"].search([])
        return [(lang.code, lang.name) for lang in langs]

    def _compute_incoming_message(self):
        for request in self:
            messages = request.mapped("message_ids").filtered(
                lambda m, r=request: m.body
                and (m.author_id == r.partner_id or m.email_from == r.email_from)
            )
            message = request.incoming_message_id = messages[:1]
            request.incoming_message = message.body
            from_email = message.email_from or message.author_id.email or ""
            request.quoted_reply = f"""
                <blockquote style="padding-right:0px;padding-left:5px;
                    border-left-color: #000; margin-left:5px;
                    margin-right:0px;border-left-width: 2px; border-left-style:solid"
                >
                    From: {from_email.replace('<', '(').replace('>', ')')}<br/>
                    Date: {message.date}<br/>
                    Subject: {message.subject}<br/>
                    {message.body}
                </blockquote>
            """
            request.reply_to = message.reply_to

    def action_reply(self):
        """
        This function opens a window to compose an email, with the default
        template message loaded by default
        """
        self.ensure_one()

        if not self.partner_id:
            raise exceptions.UserError(_("You can only reply if you set the partner."))

        if not self.language:
            raise exceptions.UserError(_("Language must be specified."))

        if not self.user_id:
            self.user_id = self.env.user

        template_id = self.categ_id.template_id.id
        ctx = {
            "default_model": "crm.claim",
            "default_res_id": self.id,
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment",
            "default_partner_ids": [(4, self.partner_id.id)],
            "default_subject": self.name,
            "use_email_alias": self.reply_to or self.email_from,
            "mark_so_as_sent": True,
            "salutation_language": self.language,
            "default_body": prepend_html_content(
                self.quoted_reply,
                f"<div style='margin-bottom: 20px;'>"
                f"<p>{self.partner_id.salutation}</p></div>",
            ),
        }

        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "target": "new",
            "context": ctx,
        }

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

        if not custom_values:
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
            "name": subject,
            "email_from": msg.get("from"),
        }

        if "partner_id" not in custom_values:
            match_obj = self.env["res.partner.match"]
            partner = match_obj.match_values_to_partner(
                {"email": email_normalize(defaults["email_from"])}, match_create=False
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
        """Change the stage to "Waiting on support" when the customer writes a
        new mail on the thread, Unassign and put as "New" if the User in charge
        is in leave.
        """
        result = super().message_update(msg_dict, update_vals)
        wait_support = self.env.ref("crm_request.stage_wait_support")
        stage_new = self.env.ref("crm_claim.stage_claim1")
        in_leave = self.filtered("user_id.employee_ids.current_leave_id")
        (self - in_leave).write({"stage_id": wait_support})
        in_leave.write({"stage_id": stage_new, "user_id": False})
        return result

    def message_post(self, **kwargs):
        """Change the stage to "Resolve" when the employee answer
        to the supporter but not if it's an automatic answer.
        """
        result = super().message_post(**kwargs)
        if "mail_server_id" in kwargs and not self.env.context.get("keep_stage"):
            resolved_stage = self.env.ref("crm_claim.stage_claim2")
            self.write({"stage_id": resolved_stage.id})
        return result.id

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """Override to avoid changing the email_from value when already set.
        :param email: ignored
        """
        if self.partner_id:
            if not self.partner_phone:
                self.partner_phone = self.partner_id.phone
            if not self.email_from:
                self.email_from = self.partner_id.email

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
                # Put the partner as author of the incoming message
                request.message_ids.filtered(
                    lambda m, r=request: m.email_from == r.email_from
                ).write({"author_id": values["partner_id"]})
                # Sync partner fields
                partner = request.partner_id
                if request.email_from:
                    if partner.email and request.email_from:
                        try:
                            with self.env.cr.savepoint():
                                partner.write(
                                    {
                                        "email_alias_ids": [
                                            (0, 0, {"email": request.email_from})
                                        ]
                                    }
                                )
                        except (IntegrityError, ValidationError):
                            _logger.warning("Unable to sync email to partner")
                    else:
                        partner.email = request.email_from
                if request.partner_phone and not partner.phone:
                    partner.phone = request.partner_phone

        return True

    def send_holiday_answer(self):
        """This will use the holiday mail template and enforce a
        mail sending to the requester."""
        template = self.env.ref("crm_request.business_closed_email_template")
        for request in self:
            template.with_context(lang=request.language).send_mail(
                request.id,
                force_send=True,
                email_values={"email_to": request.email_from},
            )

    @api.model
    def cron_reminder_request(self):
        """Periodically sends a reminder to unaddressed request
        (new, waiting for support)"""

        new_stage_id = self.env.ref("crm_claim.stage_claim1").id
        wait_support_stage_id = self.env.ref("crm_request.stage_wait_support").id

        request_to_notify = self.search(
            [
                ("stage_id", "in", [new_stage_id, wait_support_stage_id]),
                ("user_id", "!=", False),
                ("user_id.do_reminder_support_req", "=", False),
                ("write_date", "<", fields.datetime.now() - relativedelta(weeks=1)),
            ]
        )

        for req in request_to_notify:
            req.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("A support request requires your attention"),
                note=_(
                    "The request {} you were assigned to requires your attention."
                ).format(req.code),
                user_id=req.user_id.id,
            )
