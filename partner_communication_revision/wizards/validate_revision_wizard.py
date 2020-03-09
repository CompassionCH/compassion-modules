##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields


class ValidateRevisionWizard(models.TransientModel):
    _name = "partner.communication.validate.proposition"
    _description = "Validate proposition wizard"

    translation_revision_id = fields.Many2one(
        "partner.communication.revision",
        default=lambda s: s._get_translations()[:1],
        readonly=False,
    )
    translator_user_id = fields.Many2one(
        "res.users", "Translator", domain=[("share", "=", False)], readonly=False
    )
    lang = fields.Selection(
        "select_lang",
        "Lang of translation",
        related="translation_revision_id.lang",
        readonly=True,
    )

    @api.model
    def select_lang(self):
        langs = self.env["res.lang"].search([])
        return [(lang.code, lang.name) for lang in langs]

    @api.model
    def _get_translations(self):
        revision = self.env["partner.communication.revision"].browse(
            self._context["active_id"]
        )
        return revision.config_id.revision_ids.filtered(lambda r: not r.user_id)

    @api.multi
    def set_translator(self):
        revision = self.env["partner.communication.revision"].browse(
            self._context["active_id"]
        )
        other_langs = self._get_translations()
        if not other_langs:
            revision.approve()
            return True

        other_langs[0].write(
            {
                "user_id": self.translator_user_id.id,
                "compare_lang": revision.lang,
                "compare_text": revision.proposition_text,
                "compare_subject": revision.subject,
            }
        )
        if len(other_langs) > 1:
            self.write(
                {
                    "translation_revision_id": other_langs[1].id,
                    "translator_user_id": False,
                }
            )
            return self._reload()
        revision.approve()
        return True

    @api.multi
    def approve(self):
        revision = self.env["partner.communication.revision"].browse(
            self._context["active_id"]
        )
        revision.approve()
        return True

    def _reload(self):
        return {
            "context": self.env.context,
            "view_type": "form",
            "view_mode": "form",
            "res_model": self._name,
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "target": "new",
        }
