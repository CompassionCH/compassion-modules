# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Sylvain Laydernier <sly.laydernier@yahoo.fr>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, tools, _

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
            'Do you currently sponsor a child ?',
            help="Please click the box if the answer is yes.")
        confirm_email = fields.Char('Confirm your email')

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
                    ]
                },
                {
                    'id': 'user',
                    'title': _('Your account'),
                    'fields': [
                        'has_sponsorship',
                    ]
                },
            ]
            return fieldset

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
                ('login', '=', value)
            ])
            if value and does_login_exists:
                return 'login', _('This email already exists, please check '
                                  'if you already have an account or contact '
                                  'us if you don\'t.')

            # No error
            return 0, 0

        #######################################################################
        #                     FORM SUBMISSION METHODS                         #
        #######################################################################
        def form_create_or_update(self):
            """Prepare values and create or update main_object."""
            write_values = self.form_extract_values()
            extra_values = self._form_purge_non_model_fields(write_values)
            # pre hook
            self.form_before_create_or_update(write_values, extra_values)
            if 'skip_create_user' in write_values:
                msg = write_values['skip_create_user']
            else:
                # Create a wizard to create a portal user
                wizard = self.env['portal.wizard'].sudo().create(
                    {'portal_id': 25}
                )
                portal_user = self.env['portal.wizard.user'].sudo().create({
                    'wizard_id': wizard.id,
                    'partner_id': write_values['partner_id'],
                    'email': extra_values['partner_email'],
                    'in_portal': True
                })
                portal_user.sudo().action_apply()
                msg = write_values['message']

            if msg and self.o_request.website:
                self.o_request.website.add_status_message(msg)
            # post hook
            self.form_after_create_or_update(write_values, extra_values)
            return self.main_object

        def form_before_create_or_update(self, values, extra_values):
            # Forbid update of an existing partner
            extra_values.update({'skip_update': True})

            super(UserRegistrationForm, self).form_before_create_or_update(
                values, extra_values)

            partner = self.env['res.partner'].sudo().browse(
                values.get('partner_id'))

            # partner has already an user linked, add skip user creation option
            if partner.user_ids:
                values.update({'skip_create_user': "This email is already "
                                                   "linked to an account."})
            # partner is sponsoring a child and answered yes on the form
            elif extra_values['has_sponsorship'] and partner.has_sponsorships:
                values.update({'message': "Your account has been successfully "
                                          "created, you will now receive an "
                                          "email to finalize your "
                                          "registration."
                               })
            # partner is not sponsoring a child and answered yes (form)
            elif extra_values['has_sponsorship']:
                # TODO AP-102 :Ask child ref to try to get a match
                values.update({'skip_create_user': "This sponsor has no "
                                                   "sponsorships attached."})

            # partner is sponsoring a child and answered no on the form,
            # add skip user creation option
            elif partner.has_sponsorships:
                values.update({'skip_create_user': "Mismatch, please check the"
                                                   " form and submit it again."
                                                   "If the issue persists,"
                                                   " please contact us."
                               })
            # partner is not sponsoring a child and answered no on the form,
            # add skip user creation option
            else:
                values.update({'message': "Your account has been successfully "
                                          "created, you will now receive an "
                                          "email to finalize your "
                                          "registration."
                               })

        def form_next_url(self, main_object=None):
            """URL to redirect to after successful form submission."""
            return '/'

        def form_check_permission(self):
            return True
