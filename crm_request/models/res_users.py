##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    do_reminder_support_req = fields.Boolean(
        "Activate the reminder on support request",
        help="Define if you receive scheduled actions on the support request "
        "you're assigned to",
        default=True,
    )

    @property
    def SELF_READABLE_FIELDS(self):
        # Shown in "My Profile": without it, the user's own HR fields are
        # refused there (T3604).
        return super().SELF_READABLE_FIELDS + ["do_reminder_support_req"]
