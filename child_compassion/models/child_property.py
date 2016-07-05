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


from openerp import api, models, fields


class ChildProperty(models.TransientModel):
    """ A child property is a class linked to children to describe
    the child hobbies/activities/etc... in several languages. """
    _name = 'child.property'
    _inherit = 'connect.multipicklist'
    res_model = 'compassion.child'
    value = fields.Char(translate=True)


class HouseholdDuty(models.Model):
    _name = 'child.household.duty'
    _inherit = 'child.property'
    _description = 'Household Duty'
    res_field = 'duty_ids'


class ProjectActivity(models.Model):
    _name = 'child.project.activity'
    _inherit = 'child.property'
    _description = 'Project Activity'
    res_field = 'activity_ids'


class SchoolSubject(models.Model):
    _name = 'child.school.subject'
    _inherit = 'child.property'
    _description = 'Household Duty'
    res_field = 'subject_ids'


class ChildHobby(models.Model):
    _name = 'child.hobby'
    _inherit = 'child.property'
    _description = 'Child Hobby'
    res_field = 'hobby_ids'


class ChristianActivity(models.Model):
    _name = 'child.christian.activity'
    _inherit = 'child.property'
    res_field = 'christian_activity_ids'


class PhysicalDisability(models.Model):
    _name = 'child.physical.disability'
    _inherit = 'child.property'
    res_field = 'physical_disability_ids'


class ChronicIllness(models.Model):
    _name = 'child.chronic.illness'
    _inherit = 'child.property'
    res_field = 'chronic_illness_ids'


class MajorField(models.Model):
    _name = 'child.major.field'

    name = fields.Selection([
        ('Birthdate', 'Birthdate'),
        ('Chronic Disabilities', 'Chronic Disabilities'),
        ('Chronic Illness', 'Chronic Illness'),
        ('First Name', 'First Name'),
        ('Formal Education Level', 'Formal Education Level'),
        ('Gender', 'Gender'),
        ('Last Name', 'Last Name'),
        ('Planned Completion Date', 'Planned Completion Date'),
        ('Preferred Name', 'Preferred Name'),
    ], required=True)
    old_value = fields.Char()
    child_id = fields.Many2one('compassion.child', required=True)

    @api.model
    def create(self, vals):
        major_field = super(MajorField, self).create(vals)
        old_value = major_field.get_field_value()
        if not isinstance(old_value, basestring):
            old_value = ','.join(old_value.mapped('value'))
        major_field.old_value = old_value
        return major_field

    @api.model
    def get_field_mapping(self):
        return {
            'Birthdate': 'birthdate',
            'Chronic Disabilities': 'physical_disability_ids.value',
            'Chronic Illness': 'chronic_illness_ids.value',
            'First Name': 'firstname',
            'Formal Education Level': 'formal_education',
            'Gender': 'gender',
            'Last Name': 'lastname',
            'Planned Completion Date': 'completion_date',
            'Preferred Name': 'preferred_name',
        }

    @api.multi
    def get_field_value(self):
        values = list()
        for revision in self:
            field_mapping = revision.get_field_mapping()
            child = revision.child_id.with_context(
                lang=revision.child_id.sponsor_id.lang or 'en_US')
            values.extend(child.mapped(field_mapping[revision.name]))
        return ', '.join(map(str, values))
