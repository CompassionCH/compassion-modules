##############################################################################
#
#    Copyright (C) 2023-2026 Compassion CH (http://www.compassion.ch)
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


class TranslationPlatformController(http.Controller):
    @http.route(
        ["/translation-platform", "/translation-platform/<path:page>"],
        type="http",
        auth="public",
    )
    def translation_platform(self, page=""):
        """Serve the built translation-platform-web SPA from
        `static/tp/`.

        `static/tp/` is the destination for the `npm run build`
        output of the external translation-platform-web repo: copy
        the `dist/` folder there at release time. The webapp itself
        does client-side routing; this controller only serves
        `index.html` for app routes and redirects asset URLs into
        `/sbc_translation/static/tp/...`.
        """
        if (
            "assets" in page or page.endswith(".png") or page.endswith(".jpg")
        ):
            return redirect(f"/sbc_translation/static/tp/{page}")
        with file_open("sbc_translation/static/tp/index.html") as app:
            return app.read()
