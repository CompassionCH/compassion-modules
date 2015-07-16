# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Kevin Cristi
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import models, fields


class project_age_group(models.Model):
    """ This section provides the school schedule of children
        according to their age.
        It will display the school days and school months. """

    _name = 'compassion.project.age.group'

    project_id = fields.Many2one(
        'compassion.project', 'Project',
        required=True, ondelete='cascade')
    low_age = fields.Integer()
    high_age = fields.Integer()
    school_hours = fields.Integer('Weekly school hours')
    school_months_ids = fields.Many2many(
        'compassion.translated.value', 'project_age_group_to_value',
        'project_age_group_id', 'value_id', 'School months',
        domain=[('property_name', '=', 'school_months')])
    school_days_ids = fields.Many2many(
        'compassion.translated.value', 'project_age_group_to_value',
        'project_age_group_id', 'value_id', 'School days',
        domain=[('property_name', '=', 'school_days')])
