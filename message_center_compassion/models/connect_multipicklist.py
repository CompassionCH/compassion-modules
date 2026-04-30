##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import api, fields, models


class ConnectMultipicklist(models.AbstractModel):
    _name = "connect.multipicklist"
    _description = "Connect Multipicklist"
    _inherit = ["mail.activity.mixin", "mail.thread"]

    name = fields.Char(required=True, translate=False, index=True)
    res_model = "connect.multipicklist"
    res_field = "id"

    _sql_constraints = [
        (
            "name_uniq",
            "UNIQUE(name)",
            "You cannot have two picklist values with same name.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Sometimes we get from Connect a same value in several fields trying to
        create at the same time. We therefore try to find an already existing record
        before creating a new one, to avoid errors."""
        res = self.browse()
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        for vals in vals_list:
            name = vals["name"]
            rec = self.search([("name", "=ilike", name)])
            if not rec:
                rec = self.search([("name", "=ilike", name.replace(" ", ""))])
            if rec:
                res += rec
            else:
                res += super().create(vals)
        return res
