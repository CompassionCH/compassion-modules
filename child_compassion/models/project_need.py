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


class ProjectNeed(models.Model):
    _name = 'compassion.project.need'
    _description = 'Project Need'
    _order = 'fulfillment_date desc'

    needs_association_id = fields.Char(required=True)
    project_id = fields.Many2one(
        'compassion.project', required=True, ondelete='cascade')
    need = fields.Char()
    need_category = fields.Char()
    fulfillment_date = fields.Date()
    severity = fields.Selection([
        ('Very High', 'Very High'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ])
    comments = fields.Char()
