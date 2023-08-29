##############################################################################
#
#    Copyright (C) 2014-2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class SurveyQuestion(models.Model):
    _inherit = "survey.question"

    # when used this field tells the validation process that the maximum number of
    # option answer should be validated
    max_checked_option = fields.Integer(
        "Maximum answers",
        help="if set, maximum number of options allowed for the user"
    )

    def _validate_choice(self, answer, comment):
        # call super() function to avoid missing important behaviour
        errors = super()._validate_choice(answer, comment)
        # add check for maximum number of answered option.
        if self.max_checked_option and len(answer) > self.max_checked_option:
            errors.update({self.id: self.constr_error_msg})
        return errors


class SurveyQuestionAnswer(models.Model):
    _inherit = "survey.question.answer"

    value_right = fields.Char("Suggested value (counter-proposition)", translate=True,
                              help="Used in Matrix questions for adding a label at the last column.")


class SurveyUserInputLine(models.Model):
    _inherit = "survey.user_input.line"

    partner_id = fields.Many2one(
        related="user_input_id.partner_id", store=True, readonly=False
    )
