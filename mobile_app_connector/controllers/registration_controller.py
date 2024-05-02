##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Sylvain Laydernier <sly.laydernier@yahoo.fr>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.addons.cms_form.controllers.main import WizardFormControllerMixin

from odoo import http
from odoo.http import Controller, request


class RegistrationController(Controller, WizardFormControllerMixin):
    @http.route(
        ["/registration/page/<int:page>", "/registration/", ],
        type="http",
        auth="public",
        website=True,
        sitemap=False
    )
    def registration(self, model_id=None, **kw):
        """Handle a wizard route.
        """
        request.session["should_save"] = True
        return self.make_response("cms.form.res.users", model_id=model_id, **kw)

    @http.route("/registration/confirm", type="http", auth="public", website=True,
                sitemap=False)
    def registration_confirm(self, **kw):
        storage = request.session.get("cms.form.res.users", {}).get("steps", {})
        source = storage.get(1, {}).get("source") or storage.get(2, {}).get("source")
        return request.render(
            "mobile_app_connector.mobile_registration_success", {"source": source})
