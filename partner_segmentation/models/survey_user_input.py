##############################################################################
#
#    Copyright (C) 2014-2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon <gigon.quentin@gmail.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from collections import defaultdict

from odoo import models


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    def write(self, vals):
        out = super().write(vals)

        # compute segment affinity if needed
        is_done = vals.get("state") == "done"
        segment_survey = self.env.ref(
            "partner_segmentation.partner_segmentation_survey"
        )

        for user_input in self:
            if user_input.survey_id == segment_survey and is_done:
                ans = user_input._get_answer_as_array()
                self.env["res.partner.segment.affinity"].segment_affinity_engine(
                    ans, user_input.partner_id.id
                )

        return out

    def _get_answer_as_array(self):
        """
        Transforms a survey input into an array with input_line marks.
        Used mainly for segmentation computation with segmentation survey.
        :return: an array containing line_input marks
        """
        options_dict = defaultdict(
            lambda: []
        )  # Store options for multiple_choice questions

        for user_input_line in self.user_input_line_ids:
            question_type = user_input_line.question_id.question_type
            question = user_input_line.question_id

            if question_type == "matrix":
                options_dict[question.id].append(user_input_line.answer_score)

            elif question_type == "multiple_choice":
                if question.id not in options_dict:
                    options_dict[question.id] = question._create_options_array()

                if (
                    question.comment_count_as_answer
                    and user_input_line.answer_type == "text_box"
                ):
                    options_dict[question.id][-1] = 1
                else:
                    options_dict[question.id][
                        user_input_line.suggested_answer_id.sequence
                    ] = user_input_line.answer_score

        return [item for sublist in options_dict.values() for item in sublist]
