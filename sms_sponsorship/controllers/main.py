# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import werkzeug

from odoo.addons.cms_form.controllers.main import FormControllerMixin
from odoo.addons.website_portal.controllers.main import website_account
from odoo import http
from odoo.http import request, route


class SmsSponsorshipWebsite(website_account, FormControllerMixin):

    @route('/sms-sponsorship/<model("recurring.contract"):sponsorship>/',
           auth='public', website=True)
    def sms_partner_register(self, sponsorship=None, **kwargs):

        '''
        values = kwargs.copy()
        sponsorship = values.get('recurring.contract')
        values.update({
            'partner_id': sponsorship.partner_id
        })
        registration_form = self.get_form('sms.registration', **values)

        if sponsorship.partner_id and sponsorship.correspondent_id:
            # fill form with partner information
            registration_form.form_init(request, **values)

        registration_form.form_process()
        if registration_form.form_success:
            # The user submitted a registration, redirect to confirmation
            result = werkzeug.utils.redirect(
                registration_form.form_next_url(), code=303)
        else:
            values.update({
                'form': registration_form
            })
            result = request.render('', values)

        return self._form_redirect(result)'''

        model = 'recurring.contract'
        # kwargs['form_model_key'] = model
        return self.make_response(
            model, model_id=sponsorship and sponsorship.id, **kwargs)