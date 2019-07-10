# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Sylvain Laydernier <sly.laydernier@yahoo.fr>
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, tools, _
from odoo.exceptions import ValidationError

import logging
import re

logger = logging.getLogger(__name__)

testing = tools.config.get('test_enable')

# prevent these forms to be registered when running tests
if not testing:

    class UserRegistrationForm(models.AbstractModel):
        """
        A form allowing to register an user account and link it to an existing
        partner
        """
        _name = 'cms.form.res.users'
        _inherit = 'cms.form.match.partner'

        _form_model = 'res.users'
        _form_required_fields = 'confirm_email'
        _display_type = 'full'

        has_sponsorship = fields.Boolean(
            'Do you currently sponsor a child?',
            help="Please click the box if the answer is yes.")
        confirm_email = fields.Char('Confirm your email')
        gtc_accept = fields.Boolean(
            "Terms and conditions", required=True
        )

        @property
        def form_title(self):
            return _("Mobile app account registration")

        @property
        def _form_fieldsets(self):
            fieldset = [
                {
                    'id': 'partner',
                    'title': _('Your personal data'),
                    'fields': [
                        'partner_title',
                        'partner_firstname',
                        'partner_lastname',
                        'partner_email',
                        'confirm_email',
                        'partner_street',
                        'partner_zip',
                        'partner_city',
                        'partner_country_id',
                        'partner_birthdate'
                    ]
                },
                {
                    'id': 'user',
                    'title': _('Your account'),
                    'fields': [
                        'has_sponsorship',
                        'gtc_accept'
                    ]
                },
            ]
            return fieldset

        @property
        def form_widgets(self):
            # GTC field widget
            res = super(UserRegistrationForm, self).form_widgets
            res.update({
                'gtc_accept': 'cms_form_compassion.form.widget.terms',
                'partner_birthdate': 'cms.form.widget.date.ch',
            })
            return res

        @property
        def gtc(self):
            statement = self.env['compassion.privacy.statement'].sudo().search(
                [], limit=1)
            return statement.text

        #######################################################################
        #                      FORM'S FIELDS VALIDATION                       #
        #######################################################################

        def _form_validate_partner_email(self, value, **req_values):
            # check if value is a correct email address
            if value and not re.match(r'[^@]+@[^@]+\.[^@]+', value):
                return 'email', _('Verify your e-mail address')

            # check if email and confirm_email correspond
            if value and req_values['confirm_email'] != value:
                return 'email', _('Emails fields don\'t match')

            # check if the email is already used as login for an account
            does_login_exists = self.env['res.users'].sudo().search([
                ('login', '=', value),
                ('login_date', '!=', False)
            ])
            if value and does_login_exists:
                return 'login', _(
                    "This email is already linked to an account.")

            # No error
            return 0, 0

        #######################################################################
        #                     FORM SUBMISSION METHODS                         #
        #######################################################################
        def form_before_create_or_update(self, values, extra_values):
            # Forbid update of an existing partner
            extra_values.update({'skip_update': True})

            super(UserRegistrationForm, self).form_before_create_or_update(
                values, extra_values)

            partner = self.env['res.partner'].sudo().browse(
                values.get('partner_id'))

            # partner has already an user linked, add skip user creation option
            if any(partner.user_ids.mapped('login_date')):
                raise ValidationError(
                    _("This email is already linked to an account."))

            # partner is not sponsoring a child and answered yes (form)
            has_sponsorship = extra_values['has_sponsorship']
            if has_sponsorship and not partner.has_sponsorships:
                # TODO AP-102 :Ask child ref to try to get a match
                raise ValidationError(_(
                    "We couldn't find your sponsorships. Please contact "
                    "us for setting up your account."))

            # Push the email for user creation
            values['email'] = extra_values['partner_email']

        def _form_create(self, values):
            """ Here we create the user using the portal wizard or
            reactivate existing users that never connected. """
            existing_users = self.env['res.users'].sudo().search([
                ('login_date', '=', False),
                '|', ('partner_id', '=', values['partner_id']),
                ('login', '=', values['email'])
            ])
            if existing_users:
                self._reactivate_users(existing_users)
                self.main_object = existing_users[:1]
            else:
                wizard = self.env['portal.wizard'].sudo().create({
                    'portal_id': self.env['res.groups'].sudo().search([
                        ('is_portal', '=', True)], limit=1).id
                })
                portal_user = self.env['portal.wizard.user'].sudo().create(
                    self._get_portal_user_vals(wizard.id, values))
                portal_user.action_apply()
                self.main_object = portal_user.user_id

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
                'wizard_id': wizard_id,
                'partner_id': form_values['partner_id'],
                'email': form_values['email'],
                'in_portal': True
            }

        def form_after_create_or_update(self, values, extra_values):
            """ Mark the privacy statement as accepted.
            """
            super(UserRegistrationForm,
                  self).form_after_create_or_update(values, extra_values)
            partner = self.env['res.partner'].sudo().browse(
                values.get('partner_id')).exists()
            partner.set_privacy_statement(origin='mobile_app')

        def form_next_url(self, main_object=None):
            """URL to redirect to after successful form submission."""
            return '/'

        def form_check_permission(self):
            """Always allow access to the form"""
            return True

        @property
        def form_msg_success_created(self):
            return _(
                "Your account has been successfully created, you will now "
                "receive an email to finalize your registration."
            )
