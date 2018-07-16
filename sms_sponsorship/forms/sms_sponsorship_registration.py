# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')


if not testing:
    class PartnerSmsRegistrationForm(models.AbstractModel):
        _name = 'cms.form.sms.sponsorship.registration'
        _inherit = 'cms.form.match.partner'

        paiement_method = fields.Selection(selection=[
            ('lsv', 'LSV'), ('perm_ord', 'Permanent order')], required=True)
        pay_first_month_ebanking = fields.Boolean("Pay first month with "
                                                  "e-banking ?")
        immediately_add_gifts = fields.Boolean("Directly send gifts to the "
                                               "child ?")

        def _form_validate_payement_method(self, value, **req_values):
            if self.paiement_method != 'lsv' or \
            self.paiement_method != 'perm_ord':
                return 'payement_method', _('Please enter a valid payement '
                                            'method (LSV or permanent order')
            # No error
            return 0, 0

        def form_init(self, request, main_object=None, **kw):
            form = super(PartnerSmsRegistrationForm, self).form_init(
                request, main_object, **kw)
            # Set default values
            form.pay_first_month_ebanking = False
            form.immediately_add_gifts = False
            return form

        def form_before_create_or_update(self, values, extra_values):
            super(PartnerSmsRegistrationForm, self).form_before_create_or_update(
                values, extra_values)

            partner_id = values.get('partner_id')
            correspondent_id = values.get('correspondent_id')

            # form is already filled
            if partner_id and correspondent_id:
                if not self.partner_id:
                    self.partner_id = partner_id
                if not self.correspondent_id:
                    self.correspondent_id = correspondent_id
                return True
