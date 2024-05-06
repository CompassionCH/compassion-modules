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


class RegistrationController(Controller):
    @http.route(
        [
            "/registration/page/<int:page>",
            "/registration/",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def registration(self, model_id=None, **kw):
        """Handle a wizard route."""
        return request.redirect("/web/signup/")
