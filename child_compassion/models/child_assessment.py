# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import models, fields, api

from openerp.addons.message_center_compassion.mappings import base_mapping as \
    mapping


class ChildAssessment(models.Model):
    """ A child CDPR (Child Development Progress Report) """
    _name = 'compassion.child.cdpr'
    _description = 'Child CDPR Assessment'
    _order = 'date desc'

    assesment_type = fields.Char()
    child_id = fields.Many2one(
        'compassion.child', 'Child', required=True, ondelete='cascade'
    )
    date = fields.Datetime()
    age = fields.Char()
    physical_score = fields.Char()
    cognitive_score = fields.Char()
    spiritual_score = fields.Char()
    sociological_score = fields.Char('Socio-Emotional score')
    cdpr_age_group = fields.Char()
    source_kit_name = fields.Char()

    @api.model
    def process_commkit(self, commkit_data):
        child_assessment_mapping = mapping.new_onramp_mapping(
                                                self._name,
                                                self.env,
                                                'beneficiary_cdpr')
        vals = child_assessment_mapping.get_vals_from_connect(commkit_data)
        child = self.env['compassion.child'].search([(
            'global_id',
            '=',
            vals.get('child_id')
        )])
        vals['child_id'] = child.id
        child_assessment = self.create(vals)
        return child_assessment
