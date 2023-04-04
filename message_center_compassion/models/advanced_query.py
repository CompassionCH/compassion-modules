##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class QueryFilter(models.TransientModel):
    _name = "compassion.query.filter"
    _inherit = "compassion.mapped.model"
    _description = "Compassion Query"

    model = fields.Char()
    field_id = fields.Many2one("ir.model.fields", "Field", readonly=False)
    field_type = fields.Selection(related="field_id.ttype", readonly=True)
    operator_id = fields.Many2one(
        "compassion.query.operator", "Operator", readonly=False
    )
    operator = fields.Char(related="operator_id.gmc_name")
    start_date = fields.Date()
    end_date = fields.Date()
    value = fields.Char(help="Separate values with ;")

    @api.onchange("start_date", "end_date")
    def onchange_dates(self):
        if self.start_date:
            value = self.start_date
            if self.end_date:
                value += ";" + self.end_date
            self.value = value
    
    def data_to_json(self, mapping_name=None):
        # Queries should always be lists
        result = []
        for query in self:
            query_json = super(QueryFilter, query).data_to_json(mapping_name)
            # Value is always a list
            query_json["Value"] = query_json["Value"].split(";")
            result.append(query_json)
        return result


class QueryOperator(models.Model):
    """ An operator, valid for certain field types. """

    _name = "compassion.query.operator"
    _description = "Compassion Query Operator"

    name = fields.Char(required=True)
    gmc_name = fields.Char(required=True, translate=False)
    field_types_supported = fields.Char(required=True)
