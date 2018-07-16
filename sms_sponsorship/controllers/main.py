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
from odoo.http import request, route


class MuskathlonWebsite(FormControllerMixin):

    @route('sms-sponsorship/<model("recurring.contract"):registration',
           auth='public', website=True)
    def sms_partner_register(self, **kwargs):
        values = kwargs.copy()

        registration_form = self.get_form('sms.registration', **values)
        registration_form.form_process()

        if registration_form.form_success:
            # The user submitted a registration, redirect to confirmation
            result = werkzeug.utils.redirect(
                registration_form.form_next_url(), code=303)
        else:
            values.update({
                'form': registration_form
            })
            result = request.render('a_certain_view', values)

        return self._form_redirect(result)