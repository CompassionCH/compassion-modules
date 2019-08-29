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
        _inherit = ['cms.form.wizard', 'cms.form.match.partner']

        _wiz_name = _name
        form_buttons_template = 'mobile_app_connector.' \
                                'mobile_form_buttons_registration'

        _wiz_step_stored_fields = ()

        def wiz_configure_steps(self):
            return {
                1: {'form_model': 'registration.base.form'},
                2: {'form_model': 'registration.supporter.form'},
                3: {'form_model': 'registration.not.supporter'},
            }

        def wiz_next_step(self):
            return None

        def wiz_prev_step(self):
            return 1

        def form_next_url(self, main_object=None):
            direction = self.request.form.get('wiz_submit', 'next')
            if direction == 'next':
                step = self.wiz_next_step()
            else:
                step = self.wiz_prev_step()
            if not step:
                # validate form
                return '/'
            return self._wiz_url_for_step(step, main_object=main_object)

        def _wiz_base_url(self):
            return '/registration'

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

        @property
        def form_title(self):
            return _("Mobile app account registration")

        #######################################################################
        #                      FORM'S FIELDS VALIDATION                       #
        #######################################################################
        def _form_validate_partner_email(self, value, **req_values):
            # check if value is a correct email address
            if value and not re.match(r'[^@]+@[^@]+\.[^@]+', value):
                return 'email', _('Verify your e-mail address')

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

        def form_after_create_or_update(self, values, extra_values):
            """ Mark the privacy statement as accepted.
            """
            super(UserRegistrationForm, self).form_after_create_or_update(
                values, extra_values)
            if self.form_next_url() == '/':  # form submitted
                partner = self.env['res.partner'].sudo().browse(
                    values.get('partner_id')).exists()
                partner.set_privacy_statement(origin='mobile_app')

        def form_check_permission(self):
            """Always allow access to the form"""
            return True

        @property
        def form_msg_success_created(self):
            if self.form_next_url() == '/':  # form submitted
                return _(
                    "Your account has been successfully created, you will now "
                    "receive an email to finalize your registration."
                )
            else:  # form not submitted (previous)
                return None

        def form_validate(self, request_values=None):
            if self.form_next_url() == '/':  # form submitted
                return super(UserRegistrationForm, self).form_validate(
                    request_values)
            else:  # form not submitted (previous)
                return 0, 0

    class RegistrationBaseForm(models.AbstractModel):
        """
        Registration form base
        """

        _name = 'registration.base.form'
        _inherit = 'cms.form.res.users'

        _nextPage = 1

        has_sponsorship = fields.Selection(
            [('yes', 'Yes'), ('no', 'No')],
            'Do you currently sponsor a child?',
            required=True
        )

        @property
        def _form_fieldsets(self):
            fieldset = [
                {
                    'id': 'user',
                    'fields': [
                        'has_sponsorship',
                    ]
                },
            ]
            return fieldset

        def wiz_current_step(self):
            return 1

        def wiz_next_step(self):
            return self._nextPage

        def wiz_prev_step(self):
            return None

        def form_before_create_or_update(self, values, extra_values):
            if values['has_sponsorship'] == 'yes':
                self._nextPage = 2
            else:
                self._nextPage = 3

        def _form_create(self, values):
            pass

    class RegistrationNotSupporter(models.AbstractModel):
        """
        Registration form for new users
        """

        _name = 'registration.not.supporter'
        _inherit = 'cms.form.res.users'

        _form_model = 'res.users'
        _display_type = 'full'

        gtc_accept = fields.Boolean(
            "Terms and conditions", required=True
        )

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
                        'partner_street',
                        'partner_zip',
                        'partner_city',
                        'partner_country_id',
                        'partner_birthdate',
                        'gtc_accept',
                    ]
                },
            ]
            return fieldset

        def wiz_current_step(self):
            return 3

        #######################################################################
        #                     FORM SUBMISSION METHODS                         #
        #######################################################################
        def form_before_create_or_update(self, values, extra_values):
            if self.form_next_url() == '/':  # form submitted
                # Forbid update of an existing partner
                extra_values.update({'skip_update': True})

                super(RegistrationNotSupporter,
                      self).form_before_create_or_update(values, extra_values)

                partner = self.env['res.partner'].sudo().browse(
                    values.get('partner_id'))

                # partner has already an user linked, add skip user creation
                # option
                if any(partner.user_ids.mapped('login_date')):
                    raise ValidationError(
                        _("This email is already linked to an account."))

                # Push the email for user creation
                values['email'] = extra_values['partner_email']

        def _form_create(self, values):
            """ Here we create the user using the portal wizard or
            reactivate existing users that never connected. """
            if self.form_next_url() == '/':
                super(RegistrationNotSupporter, self)._form_create(values)

    class RegistrationSupporterForm(models.AbstractModel):
        """
        Registration form for people that are supporters
        """

        _name = 'registration.supporter.form'
        _inherit = 'cms.form.res.users'

        _form_model = 'res.users'
        _form_required_fields = ['partner_email', 'gtc_accept']
        _display_type = 'full'

        gtc_accept = fields.Boolean(
            "Terms and conditions", required=True
        )

        @property
        def _form_fieldsets(self):
            fieldset = [
                {
                    'id': 'partner',
                    'title': _('Your personal data'),
                    'fields': [
                        'partner_email',
                        'gtc_accept',
                    ]
                },
            ]
            return fieldset

        def wiz_current_step(self):
            return 2

        def form_next_url(self, main_object=None):
            direction = self.request.form.get('wiz_submit', 'next')
            if direction == 'next':
                return '/'
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
            if self.form_next_url() == '/':  # form submitted
                # Find sponsor given the e-mail
                partner = self.env['res.partner'].sudo().search([
                    ('email', 'ilike', extra_values['partner_email']),
                    ('has_sponsorships', '=', True)
                ])

                # partner has already an user linked, add skip user creation
                # option
                if any(partner.mapped('user_ids.login_date')):
                    raise ValidationError(
                        _("This email is already linked to an account."))
                # partner is not sponsoring a child (but answered yes (form))
                if not partner or len(partner) > 1:
                    # TODO AP-102 :Ask child ref to try to get a match
                    link_text = 'Click here to send the template ' \
                                'email request.'
                    to = 'info@compassion.ch'
                    subject = 'Account Setup: User Not Found'
                    body = 'Please set my mobile app account with the ' \
                           'following email address: %22' + str(
                            extra_values['partner_email']) + '%22'
                    raise ValidationError(_(
                        "We couldn't find your sponsorships. Please contact "
                        "us for setting up your account. " +
                        self._add_mailto(link_text, to, subject, body)))

                # Push the email for user creation
                values['email'] = extra_values['partner_email']
                values['partner_id'] = partner.id

        def _form_create(self, values):
            """ Here we create the user using the portal wizard or
            reactivate existing users that never connected. """
            if self.form_next_url() == '/':
                super(RegistrationSupporterForm, self)._form_create(values)

        def _add_mailto(self, link_text, to, subject, body):
            subject_mail = subject.replace(' ', '%20')
            body_mail = body.replace(' ', '%20')
            return '<a href="mailto:' + to + '?subject=' + subject_mail + \
                   '&body=' + body_mail + '">' + link_text + '</a>'
