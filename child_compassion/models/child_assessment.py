# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import models, fields, api

from ..mappings.child_assessment_mapping import ChildAssessmentMapping


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
        child_assessment_mapping = ChildAssessmentMapping(self.env)
        assessment_ids = list()
        for cdpr_data in commkit_data.get(
                'BeneficiaryAssessmentResponseList', [commkit_data]):
            vals = child_assessment_mapping.get_vals_from_connect(cdpr_data)
            child_assessment = self.create(vals)
            assessment_ids.append(child_assessment.id)
        return assessment_ids
