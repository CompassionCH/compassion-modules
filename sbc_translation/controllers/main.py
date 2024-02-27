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
from odoo.tools import file_open

_logger = logging.getLogger(__name__)


class RestController(http.Controller):
    @http.route(
        ["/translation-platform", "/translation-platform/<path:page>"],
        type="http",
        auth="public",
    )
    def translation_platform(self, page=""):
        """
        Simple server for the translation platform which should be compiled into /static/tp folder.
        :param page: This the route requested
        :return: index.html, or assets.
        """
        if (
            "assets" in page or page.endswith(".png") or page.endswith(".jpg")
        ):  # Serving assets
            return redirect(f"/sbc_translation/static/tp/{page}")
        with file_open("sbc_translation/static/tp/index.html") as app:
            return app.read()
