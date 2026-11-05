##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, api, models

JOB_MODEL = "partner.communication.job"


class TemplatePreview(models.TransientModel):
    _inherit = "mail.template.preview"

    def _is_communication_template(self):
        return self.mail_template_id.sudo().model == JOB_MODEL

    @api.depends("mail_template_id")
    def _compute_resource_ref(self):
        """A communication template reads the objects of its own rule (e.g. a
        registration): preview it on a communication of a rule using it, not
        on the latest communication of any rule."""
        res = super()._compute_resource_ref()
        for preview in self.filtered(lambda p: p._is_communication_template()):
            job = self.env[JOB_MODEL].search(
                [("config_id.email_template_id", "=", preview.mail_template_id.id)],
                limit=1,
            )
            preview.resource_ref = f"{JOB_MODEL},{job.id}" if job else False
        return res

    @api.depends("lang", "resource_ref")
    def _compute_mail_template_fields(self):
        res = super()._compute_mail_template_fields()
        if self._is_communication_template() and not self.resource_ref:
            self.error_msg = _(
                "No communication uses this template yet. Choose one in Record "
                "to preview it."
            )
        return res
