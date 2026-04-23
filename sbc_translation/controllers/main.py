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

from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class TranslationPlatformController(CustomerPortal):
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

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if not request.env.user.has_group("sbc_translation.group_user"):
            return values
        partner = request.env.user.partner_id
        translator = request.env["translation.user"].search(
            [("partner_id", "=", partner.id)]
        )
        if translator and "letters_to_translate" in counters:
            if translator.translation_skills:
                nb_letters = request.env["correspondence"].search_count(
                    [
                        ("state", "=", "Global Partner translation queue"),
                        ("translation_status", "=", "to do"),
                        ("new_translator_id", "=", False),
                        (
                            "translation_competence_id.skill_ids",
                            "in",
                            translator.translation_skills.ids,
                        ),
                    ]
                )
                values["letters_to_translate"] = nb_letters
            else:
                values["letters_to_translate"] = 1
        if translator and "letters_in_progress" in counters:
            nb_letters = request.env["correspondence"].search_count(
                [
                    ("state", "=", "Global Partner translation queue"),
                    ("translation_status", "!=", "done"),
                    ("new_translator_id", "=", translator.id),
                ]
            )
            values["letters_in_progress"] = nb_letters
        values["translator"] = translator
        return values
