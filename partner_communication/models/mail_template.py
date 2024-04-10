##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models, tools

_BODY_HTML = "body_html"


class MailTemplate(models.Model):
    """change generate_email to can be call with res_ids
    not only an id but with a record, this is use for the change
    of email_preview.template res_id selection to reference field"""

    _inherit = "mail.template"

    # INFO: In commit de1743ab126309d6c2b6a189305ce6a3e1e1fd18 of the odoo/odoo
    # repo they removed this field which is necessary for compassion.
    # TODO T1245: remove this field if a better solution is found or this TODO
    user_signature = fields.Boolean(
        "Add Signature",
        help="If checked, the user's signature will be appended to the text "
        "version of the message",
    )

    def generate_email(self, res_ids, fields=None):
        if isinstance(res_ids, models.BaseModel):
            res_ids = res_ids.id

        return_value = super().generate_email(res_ids, fields)

        # TODO T1245: remove this, if a better solution is found or this TODO
        signature = self.env.user.signature
        if self.user_signature and signature:
            if _BODY_HTML in return_value:
                self._append_signature(return_value, signature)
            else:
                for res_id in return_value.keys():
                    self._append_signature(return_value[res_id], signature)

        return return_value

    # TODO T1245: remove this method, if a better solution is found or this TODO
    def _append_signature(self, value, signature):
        value[_BODY_HTML] = tools.append_content_to_html(
            value[_BODY_HTML], signature, plaintext=False
        )

        if value.get(_BODY_HTML):
            value[_BODY_HTML] = tools.html_sanitize(value[_BODY_HTML])
