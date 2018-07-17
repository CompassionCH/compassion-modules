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

from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')


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
        partner_name = fields.Char('Name', required=True)
        partner_email = fields.Char('Email', required=True)
        partner_phone = fields.Char('Phone', required=True)
        partner_street = fields.Char('Street', required=True)
        partner_zip = fields.Char('Zip', required=True)
        partner_city = fields.Char('City', required=True)
        partner_country_id = fields.Many2one(
            'res.country', 'Country', required=True)
        partner_state_id = fields.Many2one(
            'res.country.state', 'State')

        def _form_load_partner_country_id(
                self, fname, field, value, **req_values):
            # Default value loaded in website form
            return int(req_values.get('partner_country_id',
                                      self.partner_country_id.id))

        def _form_validate_partner_phone(self, value, **req_values):
            if not re.match(r'^[+\d][\d\s]{7,}$', value, re.UNICODE):
                return 'phone', _('Please enter a valid phone number')
            # No error
            return 0, 0

        def _form_validate_partner_zip(self, value, **req_values):
            if not re.match(r'^\d{3,6}$', value):
                return 'zip', _('Please enter a valid zip code')
            # No error
            return 0, 0

        def _form_validate_partner_email(self, value, **req_values):
            if not re.match(r'[^@]+@[^@]+\.[^@]+', value):
                return 'email', _('Verify your e-mail address')
            # No error
            return 0, 0

        def _form_validate_partner_name(self, value, **req_values):
            return self._form_validate_alpha_field('name', value)

        def _form_validate_partner_street(self, value, **req_values):
            return self._form_validate_alpha_field('street', value)

        def _form_validate_partner_city(self, value, **req_values):
            return self._form_validate_alpha_field('city', value)

        def _form_validate_alpha_field(self, field, value):
            if not re.match(r"^[\w\s'-]+$", value, re.UNICODE):
                return field, _('Please avoid any special characters')
            # No error
            return 0, 0

        def form_init(self, request, main_object=None, **kw):
            form = super(PartnerMatchform, self).form_init(
                request, main_object, **kw)
            # Set default values
            form.partner_country_id = kw.get(
                'partner_country_id', self.env.ref('base.ch'))
            return form

        def _get_partner_vals(self, values, extra_values):
            keys = [
                'name', 'email', 'phone', 'street', 'city', 'zip',
                'country_id', 'state_id', 'title'
            ]
            return {
                key: extra_values.get(
                    'partner_' + key, values.get('partner_' + key))
                for key in keys
            }
