##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models


class MailTemplate(models.Model):
    """change generate_email to can be call with res_ids
    not only an id but with a record, this is use for the change
    of email_preview.template res_id selection to reference field"""

    _inherit = "mail.template"

    @api.multi
    def generate_email(self, res_ids, fields=None):
        if isinstance(res_ids, models.BaseModel):
            res_ids = res_ids.id

        return super().generate_email(res_ids, fields)
