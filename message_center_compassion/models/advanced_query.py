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
    _name = 'compassion.query.filter'
    _inherit = 'compassion.mapped.model'
    _description = 'Compassion Query'

    model = fields.Char()
    field_id = fields.Many2one('ir.model.fields', 'Field')
    field_type = fields.Selection(related='field_id.ttype', readonly=True)
    operator_id = fields.Many2one('compassion.query.operator', 'Operator')
    operator = fields.Char(related='operator_id.gmc_name')
    start_date = fields.Date()
    end_date = fields.Date()
    value = fields.Char(help='Separate values with ;')
    mapped_fields = fields.Many2many(
        'ir.model.fields', 'search_filter_to_fields',
        compute='_compute_mapped_fields')

    @api.onchange('start_date', 'end_date')
    def onchange_dates(self):
        if self.start_date:
            value = self.start_date
            if self.end_date:
                value += ';' + self.end_date
            self.value = value

    @api.depends('model')
    def _compute_mapped_fields(self):
        mapping_name = self.env.context.get('default_mapping_name', 'default')
        for query in self.filtered('model'):
            try:
                mapping = self.env['compassion_mapping'].search([
                    'name', '=', mapping_name
                ])
                query.mapped_fields = self.env['ir.model.fields'].search([
                    ('model', '=', query.model),
                    ('name', 'in', [n for n in mapping.json_spec_ids
                                    .field_name])
                ])
            except ValueError:
                continue

    @api.onchange('mapped_fields')
    def onchange_mapped_fields(self):
        if self.mapped_fields:
            return {
                'domain': {'field_id': [('id', 'in', self.mapped_fields.ids)]}
            }


class QueryOperator(models.Model):
    """ An operator, valid for certain field types. """
    _name = 'compassion.query.operator'
    _description = 'Compassion Query Operator'

    name = fields.Char(required=True)
    gmc_name = fields.Char(required=True, translate=False)
    field_types_supported = fields.Char(required=True)
