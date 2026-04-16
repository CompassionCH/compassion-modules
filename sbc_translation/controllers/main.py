##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from werkzeug.utils import redirect

from odoo import http

_logger = logging.getLogger(__name__)


class RestController(http.Controller):
    @http.route(
        ["/translation-platform", "/translation-platform/<path:page>"],
        type="http",
        auth="user",
    )
    def translation_platform(self, page="", **kwargs):
        """
        Legacy route: redirect old standalone-app URLs to the new Odoo 18 backend
        client action at /odoo/translation-platform.
        """
        return redirect("/odoo/translation-platform", 301)
