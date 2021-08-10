##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from pandas.tseries.offsets import BDay

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HolidayClosure(models.Model):
    _name = "holiday.closure"
    _description = "Holiday closure"
    _inherit = "translatable.model"

    start_date = fields.Date("Start of holiday", required=True)
    end_date = fields.Date("End of holiday", required=True)
    reply_date = fields.Date("Date of first reply")
    holiday_name = fields.Char("Name of holiday", required=True, translate=True)
    holiday_message = fields.Html(
        default=lambda s: s._default_message(), translate=True, sanitize=False,
        help="Use ${holiday_name}, ${start_date}, ${end_date} and ${reply_date} "
             "to replace in the text with the holiday name, start date, end date "
             "or the date at which we will be able to answer again.")

    @api.model
    def _default_message(self):
        return _("""
<p>
    Thank you for your message.
</p>
<p>
    We look forward to answering your message again from ${reply_date}.
</p>
<p>
    Until then, we wish you happy holidays.
</p>
<p>
    Best regards from the whole Compassion team
</p>        
""")

    @api.constrains("end_date", "start_date")
    def _validate_dates(self):
        for h in self:
            if h.start_date and h.end_date and (h.start_date >= h.end_date):
                raise ValidationError(
                    _("Please choose an end_date greater than the start_date")
                )

    @api.onchange("end_date")
    def onchange_end_date(self):
        if self.end_date and (not self.reply_date or self.reply_date <= self.end_date):
            self.reply_date = (self.end_date + BDay(1)).date()

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        # Make sure the translations are set for the default message
        to_translate = res.filtered(
            lambda h: h.holiday_message == self._default_message())
        langs = self.env["res.lang"].search([
            ("code", "!=", self.env.lang), ("translatable", "=", True)])
        for record in to_translate:
            for lang in langs.mapped("code"):
                record.with_context(lang=lang).holiday_message = self.with_context(
                    lang=lang)._default_message()
        return res
