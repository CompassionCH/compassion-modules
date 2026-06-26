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

    def __init__(self, pool, cr):
        """Allow users to read/write this preference on their own profile,
        even without HR Officer rights. Without this, the field breaks the
        res.users self-read bypass and the whole profile page fails with an
        AccessError for non-officer employees.
        """
        super().__init__(pool, cr)
        type(self).SELF_READABLE_FIELDS = type(self).SELF_READABLE_FIELDS + [
            "do_reminder_support_req"
        ]
        type(self).SELF_WRITEABLE_FIELDS = type(self).SELF_WRITEABLE_FIELDS + [
            "do_reminder_support_req"
        ]
