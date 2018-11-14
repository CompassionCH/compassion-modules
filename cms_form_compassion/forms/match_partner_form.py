# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from odoo import api, models, fields, tools, _

testing = tools.config.get('test_enable')


@api.model
def _lang_get(self):
    return self.env['res.lang'].sudo().get_installed()


if not testing:
    # prevent these forms to be registered when running tests

    class PartnerMatchform(models.AbstractModel):
        """A form that can create partner given data.
           It will put the found partner in field partner_id that must
           be present on the related model.
        """
        _name = 'cms.form.match.partner'
        _inherit = 'cms.form'

        partner_id = fields.Many2one('res.partner')
        partner_title = fields.Many2one(
            'res.partner.title', 'Title', required=True)
        partner_firstname = fields.Char('First Name', required=True)
        partner_lastname = fields.Char('Last Name', required=True)
        partner_email = fields.Char('Email', required=True)
        partner_phone = fields.Char('Phone', required=True)
        partner_street = fields.Char('Street', required=True)
        partner_zip = fields.Char('Zip', required=True)
        partner_city = fields.Char('City', required=True)
        partner_country_id = fields.Many2one(
            'res.country', 'Country', required=True)
        partner_state_id = fields.Many2one(
            'res.country.state', 'State')
        partner_lang = fields.Selection(_lang_get, 'Language')
        partner_birthdate = fields.Date('Birthdate')

        #######################################################################
        #            Inject default values in form from main object           #
        #######################################################################
        def _form_load_partner_id(self, fname, field, value, **req_values):
            return value or req_values.get(
                fname, self.main_object.partner_id.id)

        def _form_load_partner_firstname(self, fname, field, value,
                                         **req_values):
            return value or self._load_partner_field(fname, **req_values)

        def _form_load_partner_lastname(self, fname, field, value,
                                        **req_values):
            return value or self._load_partner_field(fname, **req_values)

        def _form_load_partner_title(self, fname, field, value, **req_values):
            read_val = value or self._load_partner_field(fname, **req_values)
            if isinstance(read_val, models.Model):
                read_val = read_val.id
            return read_val

        def _form_load_partner_email(self, fname, field, value, **req_values):
            return value or self._load_partner_field(fname, **req_values)

        def _form_load_partner_phone(self, fname, field, value, **req_values):
            return value or self._load_partner_field(fname, **req_values)

        def _form_load_partner_street(self, fname, field, value, **req_values):
            return value or self._load_partner_field(fname, **req_values)

        def _form_load_partner_zip(self, fname, field, value, **req_values):
            return value or self._load_partner_field(fname, **req_values)

        def _form_load_partner_city(self, fname, field, value, **req_values):
            return value or self._load_partner_field(fname, **req_values)

        def _form_load_partner_country_id(
                self, fname, field, value, **req_values):
            read_val = value or self._load_partner_field(fname, **req_values)
            if isinstance(read_val, models.Model):
                read_val = read_val.id
            return read_val or self.env.ref('base.ch').id

        def _form_load_partner_lang(self, fname, field, value, **req_values):
            return value or self._load_partner_field(fname, **req_values)

        def _form_load_partner_birthdate(self, fname, field, value,
                                         **req_values):
            return value or self._load_partner_field(fname, **req_values)

        def _load_partner_field(self, fname, **req_values):
            """ For inherited forms, we try to load partner fields in
            partner_id field that may exist in main_object of form. """
            partner = self.main_object.partner_id or self.env['res.partner']
            pf_name = fname.split('partner_')[1]
            return req_values.get(fname, getattr(partner.sudo(), pf_name, ''))

        #######################################################################
        #                         Field validation                            #
        #######################################################################
        def _form_validate_partner_phone(self, value, **req_values):
            if value and not re.match(r'^[+\d][\d\s]{7,}$', value, re.UNICODE):
                return 'phone', _('Please enter a valid phone number')
            # No error
            return 0, 0

        def _form_validate_partner_zip(self, value, **req_values):
            if value and not re.match(r'^\d{3,6}$', value):
                return 'zip', _('Please enter a valid zip code')
            # No error
            return 0, 0

        def _form_validate_partner_email(self, value, **req_values):
            if value and not re.match(r'[^@]+@[^@]+\.[^@]+', value):
                return 'email', _('Verify your e-mail address')
            # No error
            return 0, 0

        def _form_validate_partner_lastname(self, value, **req_values):
            return self._form_validate_alpha_field('last_name', value)

        def _form_validate_partner_firstname(self, value, **req_values):
            return self._form_validate_alpha_field('first_name', value)

        def _form_validate_partner_street(self, value, **req_values):
            return self._form_validate_alpha_field('street', value)

        def _form_validate_partner_city(self, value, **req_values):
            return self._form_validate_alpha_field('city', value)

        def _form_validate_alpha_field(self, field, value):
            if value and not re.match(r"^[\w\s'-/]+$", value, re.UNICODE):
                return field, _('Please avoid any special characters')
            # No error
            return 0, 0

        #######################################################################
        #                     FORM SUBMISSION METHODS                         #
        #######################################################################
        def form_before_create_or_update(self, values, extra_values):
            """
            Find and returns a matching partner, or create one.
            """
            super(PartnerMatchform, self).form_before_create_or_update(
                values, extra_values)
            partner_id = values.get('partner_id')
            partner_obj = self.env['res.partner'].sudo()
            partner = partner_obj
            new_partner = False
            if partner_id:
                partner = partner_obj.browse(partner_id)

            source_vals = self._get_partner_vals(values, extra_values)
            if not partner:
                partner = partner_obj.search([
                    ('email', '=ilike', source_vals['email']),
                    '|', ('active', '=', True), ('active', '=', False),
                ])
            if not partner:
                partner = partner_obj.search([
                    ('lastname', 'ilike', source_vals['lastname']),
                    ('firstname', 'ilike', source_vals['firstname']),
                    ('zip', '=', source_vals['zip']),
                    '|', ('active', '=', True), ('active', '=', False),
                ])
            if not partner or len(partner) > 1:
                # no match found or not sure which one -> creating a new one.
                source_vals['lang'] = self.env.lang
                partner = partner_obj.create(source_vals)
                new_partner = True
            else:
                # Write current values in partner without changing name
                del source_vals['title']
                del source_vals['lastname']
                del source_vals['firstname']
            self.after_partner_match(partner, new_partner, source_vals)
            values['partner_id'] = source_vals['partner_id']

        def after_partner_match(self, partner, new_partner, vals):
            """
            Called after partner is matched. Useful for updating partner
            data
            :param partner: res.partner record matched
            :param new_partner: True if a new partner was created
            :param vals: partner vals extracted from form
            :return: None
            """
            if not new_partner:
                partner.write(vals)
            # Push partner_id in values for using it in the rest
            # of form process
            vals['partner_id'] = partner.id

        #######################################################################
        #                         PRIVATE METHODS                             #
        #######################################################################
        def _get_partner_vals(self, values, extra_values):
            keys = self._get_partner_keys()
            vals = {
                key: extra_values.get(
                    'partner_' + key, values.get('partner_' + key))
                for key in keys
            }
            if 'lang' not in vals:
                vals['lang'] = self.env.lang
            return vals

        def _get_partner_keys(self):
            # Returns the partner fields used by the form
            return [
                'firstname', 'lastname', 'email', 'phone', 'street', 'city',
                'zip', 'country_id', 'state_id', 'title'
            ]
