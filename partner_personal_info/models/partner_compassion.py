##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import uuid

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    uuid = fields.Char("Personal unique identifier",
                       copy=False, index=True, readonly=True)
    privacy_statement_ids = fields.One2many(
        "privacy.statement.agreement",
        "partner_id",
        copy=False,
        readonly=False,
    )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["uuid"] = uuid.uuid4()
        return super().create(vals_list)

    def set_privacy_statement(self, origin):
        for partner in self:
            p_statement = self.env["compassion.privacy.statement"].get_current()
            contract = self.env["privacy.statement.agreement"].search(
                [
                    ["partner_id", "=", partner.id],
                    ["privacy_statement_id", "=", p_statement.id],
                ],
                order="agreement_date desc",
                limit=1,
            )
            if contract:
                contract.agreement_date = fields.Date.today()
                contract.origin_signature = origin
            else:
                self.env["privacy.statement.agreement"].create(
                    {
                        "partner_id": partner.id,
                        "agreement_date": fields.Date.today(),
                        "privacy_statement_id": p_statement.id,
                        "origin_signature": origin,
                    }
                )
