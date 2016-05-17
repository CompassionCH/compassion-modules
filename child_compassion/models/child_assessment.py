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


from openerp import models, fields


class ChildAssessment(models.Model):
    """ A child CDPR (Child Development Progress Report) """
    _name = 'compassion.child.cdpr'
    _description = 'Child CDPR Assessment'
    _order = 'date desc'

    child_id = fields.Many2one(
        'compassion.child', 'Child', required=True, ondelete='cascade')
    date = fields.Datetime()
    weight = fields.Char()
    height = fields.Char()
    age = fields.Char()
    physical_score = fields.Char()
    cognitive_score = fields.Char()
    spiritual_score = fields.Char()
    sociological_score = fields.Char('Socio-Emotional score')
