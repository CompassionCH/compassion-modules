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


from openerp import models


class ChildProperty(models.AbstractModel):
    """ A child property is a class linked to children to describe
    the child hobbies/activities/etc... in several languages. """
    _name = 'child.property'
    _inherit = 'connect.multipicklist'
    res_model = 'compassion.child'


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
