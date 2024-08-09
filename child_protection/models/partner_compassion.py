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

from odoo import fields, models
from odoo.tools.mimetypes import guess_mimetype

logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    date_agreed_child_protection_charter = fields.Datetime(
        help="The date and time when the partner has agreed to the child"
        "protection charter.",
        tracking=True,
    )
    signed_child_protection_agreement = fields.Binary(
        attachment=True,
    )
    signed_child_protection_agreement_name = fields.Char(
        compute="_compute_signed_child_protection_agreement_name"
    )
    criminal_record = fields.Binary(
        attachment=True,
    )
    criminal_record_name = fields.Char(compute="_compute_criminal_record_name")
    criminal_record_date = fields.Date(tracking=True)
    background_check = fields.Binary(
        attachment=True,
    )
    background_check_name = fields.Char(compute="_compute_background_check_name")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_signed_child_protection_agreement_name(self):
        for partner in self:
            partner.signed_child_protection_agreement_name = partner._get_file_name(
                partner.with_context(bin_size=False).signed_child_protection_agreement,
                "Child agreement",
            )

    def _compute_criminal_record_name(self):
        for partner in self:
            partner.criminal_record_name = partner._get_file_name(
                partner.with_context(bin_size=False).criminal_record,
                "Criminal record",
            )

    def _compute_background_check_name(self):
        for partner in self:
            partner.background_check_name = partner._get_file_name(
                partner.with_context(bin_size=False).background_check,
                "Background check",
            )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    def write(self, vals):
        if vals.get("criminal_record"):
            vals["criminal_record_date"] = fields.Date.today()
        return super().write(vals)

    ##########################################################################
    #                            PRIVATE METHODS                             #
    ##########################################################################
    def _get_file_name(self, file, desc):
        self.ensure_one()
        if file:
            file_type = guess_mimetype(file)
            return f"{desc} - {self.name} [{file_type}]"
        else:
            return False
