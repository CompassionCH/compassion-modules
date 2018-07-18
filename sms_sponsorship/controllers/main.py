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
        model = 'recurring.contract'
        return self.make_response(
            model, model_id=sponsorship and sponsorship.id, **kwargs)
