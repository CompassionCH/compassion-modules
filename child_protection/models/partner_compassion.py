##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import fields, models, _
from odoo.tools.mimetypes import guess_mimetype


logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    has_agreed_child_protection_charter = fields.Boolean(
        help="Indicates if the partner has agreed to the child protection" "charter.",
        default=False,
    )
    date_agreed_child_protection_charter = fields.Datetime(
        help="The date and time when the partner has agreed to the child"
        "protection charter."
    )
    criminal_record = fields.Binary(
        attachment=True,
    )
    criminal_record_name = fields.Char(compute="_compute_criminal_record_name")
    criminal_record_date = fields.Date()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def update_child_protection_charter(self, vals):
        for partner in self:
            agreed = vals.get("has_agreed_child_protection_charter")
            date = fields.Datetime.now() if agreed else None
            vals.update(
                {
                    "date_agreed_child_protection_charter": date,
                }
            )
            agreed_message = _("Has agreed to the child protection charter.")
            disagreed_message = _("Has disagreed to the child protection charter.")
            partner.message_post(
                body=agreed_message if agreed else disagreed_message,
                subject=_("Child protection charter"),
            )
        return True

    def _compute_criminal_record_name(self):
        for partner in self:
            if partner.criminal_record:
                ftype = guess_mimetype(
                    partner.with_context(bin_size=False).criminal_record
                )
                partner.criminal_record_name = f"Criminal record {partner.name}{ftype}"
            else:
                partner.criminal_record_name = False

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    def write(self, vals):
        if vals.get("criminal_record"):
            vals["criminal_record_date"] = fields.Date.today()
        if "has_agreed_child_protection_charter" in vals:
            self.update_child_protection_charter(vals)
        return super().write(vals)
