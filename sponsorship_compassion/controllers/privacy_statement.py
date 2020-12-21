##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http, _
from odoo.http import request

from odoo.addons.cms_form.controllers.main import FormControllerMixin


class PrivacyStatementController(http.Controller, FormControllerMixin):
    @http.route(
        route="/partner/<string:reg_uid>/privacy-statement-agreement",
        auth="public",
        website=True,
    )
    def privacy_statement_agreement(
            self, reg_uid, form_id=None, redirect=None, **kwargs
    ):
        """
        This page allows a partner to sign the child protection charter.
        :param reg_uid: The uuid associated with the partner.
        :param form_id:
        :param redirect: The redirection link for the confirmation page.
        :param kwargs: The remaining query string parameters.
        :return: The rendered web page.
        """
        # Need sudo() to bypass domain restriction on res.partner for anonymous
        # users.
        partner = request.env["res.partner"].sudo().search([("uuid", "=", reg_uid)])

        if not partner:
            return request.redirect("/")

        values = kwargs.copy()

        privacy_statement_id = request.env["compassion.privacy.statement"]\
            .sudo().search([]).sorted("version")[:1]
        if not privacy_statement_id:
            raise ValueError("There is no privacy statement in database.")

        values["privacy_statement_id"] = privacy_statement_id

        form_model_key = "cms.form.partner.privacy.statement"
        # Do not use self.get_form() because it does not have sufficient rights
        # to search for the partner object (by the id).
        privacy_statement_form = request.env[form_model_key].form_init(
            request, main_object=partner, **values
        )
        privacy_statement_form.form_process()

        partner.env.clear()
        values.update(
            {
                "partner": partner,
                "privacy_statement_form": privacy_statement_form,
            }
        )

        if partner.privacy_statement_ids:
            confirmation_message = _(
                "We successfully received your agreement to the Privacy "
                "Statement."
            )

            values.update(
                {
                    "confirmation_title": _("Thank you!"),
                    "confirmation_message": confirmation_message,
                    "redirect": redirect,
                }
            )
            return request.render(
                "sponsorship_compassion." +
                "privacy_statement_agreement_confirmation_page",
                values,
            )
        else:
            return request.render(
                "sponsorship_compassion.privacy_statement_agreement_page", values
            )
