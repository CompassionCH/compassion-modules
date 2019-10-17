# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Sylvain Laydernier <sly.laydernier@yahoo.fr>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http
from odoo.http import Controller, request

from odoo.addons.cms_form.controllers.main import WizardFormControllerMixin


class RegistrationController(Controller, WizardFormControllerMixin):

    @http.route([
        '/registration/page/<int:page>',
        '/registration/',
    ], type='http', auth='public', website=True)
    def registration(self, model_id=None, **kw):
        """Handle a wizard route.
        """
        return self.make_response(
            "cms.form.res.users", model_id=model_id, **kw)

    @http.route('/registration/confirm', type='http', auth='public',
                website=True)
    def registration_confirm(self, **kw):
        return request.render(
            'mobile_app_connector.mobile_registration_success', {})
