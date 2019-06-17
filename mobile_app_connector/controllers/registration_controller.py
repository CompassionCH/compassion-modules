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
from odoo.http import Controller

from odoo.addons.cms_form.controllers.main import FormControllerMixin


class RegistrationController(Controller, FormControllerMixin):

    @http.route('/registration/', type='http', auth='public', website=True)
    def registration_form(self, **kwargs):
        """
        Return registration form
        """
        return self.make_response(
            'res.users',
            model_id=None,
            **kwargs
        )
