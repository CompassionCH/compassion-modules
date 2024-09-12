##############################################################################
#
#    Copyright (C) 2014-2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import uuid

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    uuid = fields.Char(
        "Personal unique identifier",
        copy=False,
        index=True,
        readonly=True,
        default=lambda s: uuid.uuid4(),
    )

    _sql_constraints = [
        ("uuid_uniq", "unique (uuid)", "The uuid must be unique."),
    ]
