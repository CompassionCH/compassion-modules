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
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class SurveyMailComposeMessage(models.TransientModel):
    """
    Extend the creation of a survey and reimplemented it to make the sending of
    an email optional.
    """

    _inherit = "survey.mail.compose.message"
    public = fields.Selection(
        selection_add=[
            (
                "no_email",
                "Do not send an email to the user. No public or private "
                "invitation is sent, you will have to fill the survey "
                "yourself",
            )
        ]
    )
    phone_partner_ids = fields.Many2many(
        "res.partner",
        "survey_phone_res_partner_rel",
        "wizard_id",
        "partner_id",
        string="Existing contacts",
        readonly=False,
    )

    @api.multi
    def add_new_answer(self):
        """
        Method similar to send_mail from survey.mail.compose.message.
        :return:
        """
        survey_user_input_ref = self.env["survey.user_input"]
        anonymous_group = self.env.ref(
            "portal.group_anonymous", raise_if_not_found=False
        )

        def create_token(wizard_var, partner_id, email):
            """
            Method almost identical to nested method create_token from
            survey.mail.compose.message. It creates a token for each partner
            added by the user.
            :param wizard_var: The wizard element containing the elements
            :param partner_id: The id of the partner we want to create the
                               token for
            :param email: The email from the partner
            :return: A token in the form of a uuid.
            """
            if context.get("survey_resent_token"):
                survey_user_input = survey_user_input_ref.search(
                    [
                        ("survey_id", "=", wizard_var.survey_id.id),
                        ("state", "in", ["new", "skip"]),
                        "|",
                        ("partner_id", "=", partner_id),
                        ("email", "=", email),
                    ],
                    limit=1,
                )
                if survey_user_input:
                    return survey_user_input.token
            if wizard_var.public not in ["email_private", "no_email"]:
                # not a private survey. No need to create a record as we will
                # create one each time somebody access it.
                return None
            else:
                token = uuid.uuid4().__str__()
                # create response with token
                survey_user_input = survey_user_input_ref.create(
                    {
                        "survey_id": wizard_var.survey_id.id,
                        "deadline": wizard_var.date_deadline,
                        "date_create": fields.Datetime.now(),
                        "type": "link",
                        "state": "new",
                        "token": token,
                        "partner_id": partner_id,
                        "email": email,
                    }
                )
                return survey_user_input.token

        for wizard in self:
            # check if __URL__ is in the text
            if wizard.body.find("__URL__") < 0:
                raise UserError(
                    _(
                        "The content of the text don't contain "
                        "'__URL__'. __URL__ is automatically "
                        "converted into the special url of the "
                        "survey."
                    )
                )
            context = self.env.context
            if not wizard.phone_partner_ids and context.get("default_partner_ids"):
                wizard.phone_partner_ids = context.get("default_partner_ids")
            partner_list = []
            for partner in wizard.phone_partner_ids:
                if (
                        not anonymous_group
                        or not partner.user_ids
                        or anonymous_group not in partner.user_ids[0].groups_id
                ):
                    partner_list.append({"id": partner.id, "email": partner.email})
            if not len(partner_list):
                if wizard.model == "res.partner" and wizard.res_id:
                    return False
                raise UserError(_("Please enter at least one valid " "recipient."))
            for partner in partner_list:
                create_token(wizard, partner["id"], partner["email"])

        return {"type": "ir.actions.act_window_close"}
