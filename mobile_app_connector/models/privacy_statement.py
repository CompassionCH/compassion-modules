##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields
from ..controllers.mobile_app_controller import _get_lang


class PrivacyStatementAgreement(models.Model):
    _inherit = "privacy.statement.agreement"

    origin_signature = fields.Selection(
        selection_add=[("mobile_app", "Mobile App Registration")]
    )

    def mobile_get_privacy_notice(self, **params):
        lang = _get_lang(self, params)
        return {
            "PrivacyNotice": self.env["compassion.privacy.statement"]
            .with_context(lang=lang)
            .sudo()
            .search([], limit=1)
            .text
        }
