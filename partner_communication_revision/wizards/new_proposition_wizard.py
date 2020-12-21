##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class NewRevisionProposition(models.TransientModel):
    _name = "partner.communication.new.proposition"
    _description = "New revision proposition wizard"

    lang = fields.Selection("select_lang", required=True, default=lambda s: s.env.lang)

    @api.model
    def select_lang(self):
        langs = self.env["res.lang"].search([])
        return [(lang.code, lang.name) for lang in langs]

    @api.multi
    def new_proposition(self):
        config = self.env["partner.communication.config"].browse(
            self._context["active_id"]
        )
        revisions = config.revision_ids
        if revisions.filtered(lambda r: r.state != "active"):
            raise UserError(
                _(
                    "You cannot create a new revision until current revision is "
                    "not completed"
                )
            )
        master = config.revision_ids.filtered(lambda r: r.lang == self.lang)
        master.write(
            {
                "user_id": self.env.uid,
                "correction_user_id": False,
                "is_master_version": True,
                "state": "pending",
            }
        )
        (revisions - master).write(
            {
                "state": "pending",
                "user_id": False,
                "correction_user_id": False,
                "is_master_version": False,
            }
        )
        return {
            "name": "Edit revision",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": master._name,
            "res_id": master.id,
            "context": self.with_context(
                form_view_ref="partner_communication_revision."
                              "revision_form_proposition"
            ).env.context,
            "target": "current",
        }
