##############################################################################
#
#    Copyright (C) 2019-2021 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import datetime
import re

from pandas.tseries.offsets import BDay

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HolidayClosure(models.Model):
    _name = "holiday.closure"
    _description = "Holiday closure"
    _inherit = "translatable.model"
    _rec_name = "holiday_name"

    start_date = fields.Date("Start of holiday", required=True)
    end_date = fields.Date("End of holiday", required=True)
    reply_date = fields.Date("Date of first reply")
    holiday_name = fields.Char("Name of holiday", required=True, translate=True)
    holiday_message = fields.Html(
        default=lambda s: s._default_message(),
        translate=True,
        sanitize=False,
        help="Use [holiday_name], [start_date], [end_date] and [reply_date] "
        "to replace in the text with the holiday name, start date, end date "
        "or the date at which we will be able to answer again.",
    )
    holiday_template_message = fields.Html(
        compute="_compute_holiday_template_message",
        help="Used in the template to replace keywords by actual values",
        sanitize=False,
    )
    signature = fields.Html(compute="_compute_signature", sanitize=False)

    @api.model
    def _default_message(self):
        return _(
            """
<p>
    Thank you for your message.
</p>
<p>
    We look forward to answering your message again from [reply_date].
</p>
<p>
    Until then, we wish you happy holidays.
</p>
"""
        )

    @api.constrains("end_date", "start_date")
    def _validate_dates(self):
        for h in self:
            if h.start_date and h.end_date and (h.start_date >= h.end_date):
                raise ValidationError(
                    _("Please choose an end_date greater than the start_date")
                )

    def _compute_holiday_template_message(self):
        for holiday in self:

            def var_replace(match):
                value = getattr(holiday, match.group(1), "")
                if isinstance(value, datetime.date):
                    value = holiday.get_date(match.group(1), "date_full")
                if not isinstance(value, str):
                    value = str(value)
                return value

            holiday.holiday_template_message = re.sub(
                r"\[(\w+)\]", var_replace, holiday.holiday_message
            )

    def _compute_signature(self):
        user = self.env["res.users"]
        template = self.get_holiday_template()
        if template._name == "partner.communication.config":
            omr_config = template.get_config_for_lang(self.env.lang)[0]
            user = omr_config.user_id or template.user_id
        for holiday in self:
            holiday.signature = user.signature or _("The Compassion team")

    @api.onchange("end_date")
    def onchange_end_date(self):
        if self.end_date and (not self.reply_date or self.reply_date <= self.end_date):
            self.reply_date = (self.end_date + BDay(1)).date()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        # Make sure the translations are set for the default message
        to_translate = res.filtered(
            lambda h: h.holiday_message == self._default_message()
        )
        langs = self.env["res.lang"].search([("code", "!=", self.env.lang)])
        for record in to_translate:
            for lang in langs.mapped("code"):
                record.with_context(lang=lang).holiday_message = self.with_context(
                    lang=lang
                )._default_message()
        return res

    def edit_holiday_template(self):
        """Shortcut to open the template."""
        template = self.get_holiday_template()
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": template._name,
            "res_id": template.id,
        }

    @api.model
    def get_holiday_template(self):
        """Returns the holiday template
        (either the mail.template record or partner.communication.config if
         the module is installed and a rule is linked to it).
        """
        res = self.env.ref("crm_request.business_closed_email_template")
        config_model = "partner.communication.config"
        partner_communication_installed = config_model in self.env
        if partner_communication_installed:
            config = self.env[config_model].search(
                [("email_template_id", "=", res.id)], limit=1
            )
            if config:
                res = config
        return res

    def open_preview(self):
        return {
            "name": "Preview",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "holiday.closure.template.preview",
            "context": self.env.context,
            "target": "new",
        }
