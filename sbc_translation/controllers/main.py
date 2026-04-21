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
from odoo.http import request

_logger = logging.getLogger(__name__)


class TranslationPlatformController(http.Controller):
    @http.route(
        "/my/translation-platform",
        type="http",
        auth="user",
        website=True,
    )
    def translation_platform_portal(self, **kwargs):
        """
        Portal page for the Translation Platform OWL app.
        Only accessible to authenticated users who belong to the
        sbc_translation.group_user group.
        """
        if not request.env.user.has_group("sbc_translation.group_user"):
            return redirect("/my")
        return request.render("sbc_translation.portal_translation_platform", {})

    @http.route(
        ["/translation-platform", "/translation-platform/<path:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def translation_platform_legacy(self, page="", **kwargs):
        """
        Legacy route: redirect old standalone-app URLs to the new portal page.
        """
        return redirect("/my/translation-platform", 301)
