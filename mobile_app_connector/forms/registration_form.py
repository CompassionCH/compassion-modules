##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Sylvain Laydernier <sly.laydernier@yahoo.fr>
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import re

from odoo import models, fields, _
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)


class UserRegistrationForm(models.AbstractModel):
    """
    A form allowing to register an user account and link it to an existing
    partner
    """

    _name = "cms.form.res.users"
    _inherit = ["cms.form.wizard", "cms.form.match.partner"]

    _wiz_name = _name
    form_buttons_template = (
        "mobile_app_connector." "mobile_form_buttons_registration"
    )

    _wiz_step_stored_fields = ()

    def wiz_configure_steps(self):
        return {
            1: {"form_model": "registration.base.form"},
            2: {"form_model": "registration.supporter.form"},
            3: {"form_model": "registration.not.supporter"},
        }

    def wiz_next_step(self):
        return None

    def wiz_prev_step(self):
        return 1

    def form_next_url(self, main_object=None):
        direction = self.request.form.get("wiz_submit", "next")
        if direction == "next":
            step = self.wiz_next_step()
        else:
            step = self.wiz_prev_step()
        if not step:
            # validate form
            return "/registration/confirm"
        return self._wiz_url_for_step(step, main_object=main_object)

    def _wiz_base_url(self):
        return "/registration"

    @property
    def form_widgets(self):
        # GTC field widget
        res = super().form_widgets
        res.update(
            {
                "gtc_accept": "cms_form_compassion.form.widget.terms",
                "partner_birthdate": "cms.form.widget.date.ch",
            }
        )
        return res

    @property
    def gtc(self):
        statement = (
            self.env["compassion.privacy.statement"].sudo().search([], limit=1)
        )
        return statement.text

    @property
    def form_title(self):
        return _("Mobile app account registration")

    #######################################################################
    #                      FORM'S FIELDS VALIDATION                       #
    #######################################################################
    def _form_validate_partner_email(self, value, **req_values):
        # check if value is a correct email address
        if value and not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            return "email", _("Verify your e-mail address")

        # check if the email is already used as login for an account
        does_login_exists = (
            self.env["res.users"]
                .sudo()
                .search([("login", "=", value), ("login_date", "!=", False)])
        )
        if value and does_login_exists:
            return "login", _("This email is already linked to an account.")

        # No error
        return 0, 0

    def _reactivate_users(self, res_users):
        """
        Reactivate existing users that never connected to Odoo.
        :param res_users: users recordset
        :return: None
        """
        res_users.action_reset_password()

    def _get_portal_user_vals(self, wizard_id, form_values):
        """ Used to customize the portal wizard values if needed. """
        return {
            "wizard_id": wizard_id,
            "partner_id": form_values["partner_id"],
            "email": form_values["email"],
            "in_portal": True,
        }

    def _form_create(self, values):
        """ Here we create the user using the portal wizard or
        reactivate existing users that never connected. """
        existing_users = (
            self.env["res.users"]
                .sudo()
                .search(
                [
                    ("login_date", "=", False),
                    "|",
                    ("partner_id", "=", values["partner_id"]),
                    ("login", "=", values["email"]),
                ]
            )
        )
        if existing_users:
            self._reactivate_users(existing_users)
            self.main_object = existing_users[:1]
        else:
            wizard = self.env["portal.wizard"].sudo().create({})

            portal_user = (
                self.env["portal.wizard.user"]
                    .sudo()
                    .create(self._get_portal_user_vals(wizard.id, values))
            )
            portal_user.action_apply()
            self.main_object = portal_user.user_id

    def form_after_create_or_update(self, values, extra_values):
        """ Mark the privacy statement as accepted.
        """
        super().form_after_create_or_update(values, extra_values)
        if self.form_next_url() == "/registration/confirm":
            # form submitted
            partner = (
                self.env["res.partner"]
                .sudo()
                .browse(values.get("partner_id"))
                .exists()
            )
            partner.set_privacy_statement(origin="mobile_app")

    def form_check_permission(self):
        """Always allow access to the form"""
        return True

    @property
    def form_msg_success_created(self):
        if self.form_next_url() == "/registration/confirm":
            # form submitted
            return _(
                "Your account has been successfully created, you will now "
                "receive an email to finalize your registration."
            )
        else:  # form not submitted (previous)
            return None

    def form_validate(self, request_values=None):
        if self.form_next_url() == "/registration/confirm":
            # form submitted
            return super().form_validate(request_values)
        else:  # form not submitted (previous)
            return 0, 0

    def _sanitize_email(self, email):
        return email.strip().lower()


class RegistrationBaseForm(models.AbstractModel):
    """
    Registration form base
    """

    _name = "registration.base.form"
    _inherit = "cms.form.res.users"

    _nextPage = 1

    has_sponsorship = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        "Do you currently sponsor a child?",
        required=True,
    )

    @property
    def _form_fieldsets(self):
        fieldset = [
            {"id": "user", "fields": ["has_sponsorship", ]},
        ]
        return fieldset

    def wiz_current_step(self):
        return 1

    def wiz_next_step(self):
        return self._nextPage

    def wiz_prev_step(self):
        return None

    def form_before_create_or_update(self, values, extra_values):
        if values["has_sponsorship"] == "yes":
            self._nextPage = 2
        else:
            self._nextPage = 3

    def _form_create(self, values):
        pass


class RegistrationNotSupporter(models.AbstractModel):
    """
    Registration form for new users
    """

    _name = "registration.not.supporter"
    _inherit = "cms.form.res.users"

    _form_model = "res.users"
    _display_type = "full"

    gtc_accept = fields.Boolean("Terms and conditions", required=True)

    @property
    def _form_fieldsets(self):
        fieldset = [
            {
                "id": "partner",
                "title": _("Your personal data"),
                "fields": [
                    "partner_title",
                    "partner_firstname",
                    "partner_lastname",
                    "partner_email",
                    "partner_street",
                    "partner_zip",
                    "partner_city",
                    "partner_country_id",
                    "partner_birthdate",
                    "gtc_accept",
                ],
            },
        ]
        return fieldset

    def wiz_current_step(self):
        return 3

    #######################################################################
    #                     FORM SUBMISSION METHODS                         #
    #######################################################################
    def form_before_create_or_update(self, values, extra_values):
        if self.form_next_url() == "/registration/confirm":
            # form submitted
            # Forbid update of an existing partner
            extra_values.update({"skip_update": True})

            super().form_before_create_or_update(values, extra_values)

            partner = (
                self.env["res.partner"].sudo().browse(values.get("partner_id"))
            )

            # partner has already an user linked, add skip user creation
            # option
            if any(partner.user_ids.mapped("login_date")):
                raise ValidationError(
                    _("This email is already linked to an account.")
                )

            # Push the email for user creation
            values["email"] = self._sanitize_email(extra_values["partner_email"])

    def _form_create(self, values):
        """ Here we create the user using the portal wizard or
        reactivate existing users that never connected. """
        if self.form_next_url() == "/registration/confirm":
            super()._form_create(values)


class RegistrationSupporterForm(models.AbstractModel):
    """
    Registration form for people that are supporters
    """

    _name = "registration.supporter.form"
    _inherit = "cms.form.res.users"

    _form_model = "res.users"
    _form_required_fields = ["partner_email", "gtc_accept"]
    _display_type = "full"

    gtc_accept = fields.Boolean("Terms and conditions", required=True)

    @property
    def _form_fieldsets(self):
        fieldset = [
            {
                "id": "partner",
                "title": _("Your personal data"),
                "fields": ["partner_email", "gtc_accept", ],
            },
        ]
        return fieldset

    def wiz_current_step(self):
        return 2

    def form_next_url(self, main_object=None):
        direction = self.request.form.get("wiz_submit", "next")
        if direction == "next":
            return "/registration/confirm"
        else:
            step = self.wiz_prev_step()
        if not step:
            # fallback to page 1
            step = 1
        return self._wiz_url_for_step(step, main_object=main_object)

    #######################################################################
    #                     FORM SUBMISSION METHODS                         #
    #######################################################################
    def form_before_create_or_update(self, values, extra_values):
        if self.form_next_url() == "/registration/confirm":
            # form submitted
            partner_email = self._sanitize_email(extra_values["partner_email"])

            # Find sponsor given the e-mail
            matching_partner = (
                self.env["res.partner"]
                .sudo()
                .search([("email", "ilike", partner_email)])
            )

            # Filter to partner that have sponsorships active or in creation
            partner = matching_partner.filtered(
                lambda partner: self.env["recurring.contract"].search_count(
                    [
                        "|", 
                        ("partner_id", "=", partner.id),
                        ("correspondent_id", "=", partner.id),
                        ("state", "not in", ["cancelled", "terminated"]),
                    ]
                )
            )

            # partner has already an user linked, add skip user creation
            # option
            if any(partner.mapped("user_ids.login_date")):
                raise ValidationError(
                    _("This email is already linked to an account.")
                )
            # partner is not sponsoring a child (but answered yes (form))
            if not partner or len(partner) > 1:
                email_template = self.env.ref(
                    "mobile_app_connector.email_template_user_not_found"
                ).sudo()
                link_text = _("Click here to send the template email " "request.")
                to = email_template.email_to
                subject = email_template.subject
                body = email_template.body_html.replace(
                    "%(email_address)", partner_email
                )
                href_link = self._add_mailto(link_text, to, subject, body)
                raise ValidationError(
                    _(
                        "We couldn't find your sponsorships. Please contact "
                        "us for setting up your account."
                    )
                    + " "
                    + href_link
                )

            # Push the email for user creation
            values["email"] = partner_email
            values["partner_id"] = partner.id

    def _form_create(self, values):
        """ Here we create the user using the portal wizard or
        reactivate existing users that never connected. """
        if self.form_next_url() == "/registration/confirm":
            super()._form_create(values)

    def _add_mailto(self, link_text, to, subject, body):
        subject_mail = subject.replace(" ", "%20")
        body_mail = (
            body.replace(" ", "%20").replace('"', "%22").replace("<br/>", "%0D%0A")
        )
        return (
            '<a href="mailto:'
            + to
            + "?subject="
            + subject_mail
            + "&amp;body="
            + body_mail
            + '">'
            + link_text
            + "</a>"
        )
