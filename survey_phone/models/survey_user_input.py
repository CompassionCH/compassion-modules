##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import api, models, fields, _

logger = logging.getLogger(__name__)


class SurveyUserInput(models.Model):
    """
    Add some fields to the answer view for a survey. In particular a filed for
    both mobile and phone number as well as a clickable URL to the survey page.
    """

    _inherit = ["survey.user_input", "phone.validation.mixin"]
    _name = "survey.user_input"
    _phone_name_fields = ["phone", "mobile"]

    partner_id = fields.Many2one("res.partner", string="Partner", readonly=False)
    phone = fields.Char(related="partner_id.phone", readonly=True)
    mobile = fields.Char(related="partner_id.mobile", readonly=True)
    survey_link = fields.Char(
        "Link to complete the survey", compute="_compute_survey_link"
    )

    def _compute_survey_link(self):
        """
        Recreate the private url to access the survey from the token and public
        url available in self.
        :return: Nothing
        """
        for input in self:
            input.survey_link = input.survey_id.public_url + "/" + input.token

    def action_view_answers(self):
        """ Print PDF report instead of redirecting to survey. """
        datas = {
            "active_ids": self.ids,
            "active_model": self._name,
        }
        return {
            "type": "ir.actions.report",
            "report_name": "survey_phone.survey_user_input",
            "datas": datas,
            "nodestroy": True,
        }


class SurveyUserInputLine(models.Model):
    _inherit = "survey.user_input_line"

    value_converted_text = fields.Text(compute="_compute_value_converted")

    @api.multi
    def _compute_value_converted(self):
        """ Retrieve the value as text representation for displaying it."""
        for answer in self:
            value = _("Skipped")
            if not answer.skipped:
                value = (
                    answer.value_text
                    or answer.value_number
                    or answer.value_date
                    or answer.value_free_text
                )
                if not value:
                    suggested = answer.value_suggested or answer.value_suggested_row
                    if suggested:
                        value = suggested.value

            answer.value_converted_text = value
