##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    def write(self, vals):
        out = super().write(vals)

        # compute segment affinity if needed
        is_done = vals.get("state") == "done"
        segment_survey = self.env.ref("partner_segmentation.partner_segmentation_survey")

        for user_input in self:
            if user_input.survey_id == segment_survey and is_done:
                ans = user_input._get_answer_as_array()
                self.env["res.partner.segment.affinity"].segment_affinity_engine(
                    ans, user_input.partner_id.id
                )

        return out

    def _get_answer_as_array(self):
        """
        Will transform a survey input into an array with input_line mark.
        Use mainly for segmentation computation with segmentation survey.
        :return: an array containing line_input marks
        """

        out = []
        all_options = {}

        # for each user input (one for simple_choice and multiple for multiple_choice) extract answer value as
        # store in answer_score.
        for user_input_line in self.user_input_line_ids:

            # with simple_choice type retrieving the answer is trivial
            if user_input_line.question_id.question_type == "matrix":
                out.append([user_input_line.answer_score])

            # multiple_choice require further steps. expected output (for a multiple_choice question) is an array with
            # 0 for unselected option and "answer_score" for selected option.
            elif user_input_line.question_id.question_type == "multiple_choice":

                q = user_input_line.question_id

                if q.id not in all_options:
                    # if this question as not been seen yet. create a 0 filled array with as many entry as label for
                    # this question (label = answering option). add the array to a dictionary to use it for
                    # user_input_line related to the same question.
                    all_options[q.id] = [0] * len(q.suggested_answer_ids)

                    # when comment counts as an answer add a 0 to the array
                    if q.comments_allowed and q.comment_count_as_answer:
                        all_options[q.id].append(0)

                    # append the newly created array to the output. Further modification of the array will still
                    # affect the output by reference.
                    out.append(all_options[q.id])

                if q.comment_count_as_answer and user_input_line.answer_type == "text_box":
                    # if current input is user comment append a value of 1 at the end of the array (comment always at
                    # the end).
                    all_options[q.id][-1] = 1
                else:
                    # use the field "sequence" to store the input_line.quizz mark at the correct index.
                    all_options[q.id][
                        user_input_line.suggested_answer_id.sequence
                    ] = user_input_line.answer_score

        # Flatten the output before returning it.
        return [_input for answer in out for _input in answer]
