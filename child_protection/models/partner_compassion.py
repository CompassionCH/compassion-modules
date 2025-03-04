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

logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    date_agreed_child_protection_charter = fields.Datetime(
        help="The date and time when the partner has agreed to the child"
        "protection charter.",
        tracking=True,
    )
    criminal_record = fields.Binary(
        attachment=True,
    )
    criminal_record_name = fields.Char(compute="_compute_criminal_record_name")
    criminal_record_date = fields.Date(tracking=True)

    code_of_conduct_file = fields.Binary(
        string="Code of Conduct",
        attachment=True,
        help="Upload file",
    )
    code_of_conduct_filename = fields.Char(
        string="File Name",
        compute="_compute_code_of_conduct_filename",
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_criminal_record_name(self):
        for partner in self:
            if partner.criminal_record:
                partner.criminal_record_name = f"Criminal_Record_{partner.name}"
            else:
                partner.criminal_record_name = False

    def _compute_code_of_conduct_filename(self):
        for record in self:
            if record.code_of_conduct_file:
                record.code_of_conduct_filename = f"Code_of_Conduct_{record.name}"
            else:
                record.code_of_conduct_filename = False

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    def write(self, vals):
        if vals.get("criminal_record"):
            vals["criminal_record_date"] = fields.Date.today()

        if vals.get("code_of_conduct_file"):
            for partner in self:
                if not partner.date_agreed_child_protection_charter:
                    vals["date_agreed_child_protection_charter"] = fields.Datetime.now()
        return super().write(vals)
