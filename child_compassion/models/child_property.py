##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import fields, models


class ChildProperty(models.AbstractModel):
    """A child property is a class linked to children to describe
    the child hobbies/activities/etc... in several languages."""

    _name = "child.property"
    _inherit = "connect.multipicklist"
    _description = "Child Property"
    _rec_name = "value"

    res_model = "compassion.child"
    value = fields.Char(translate=True)


class HouseholdDuty(models.Model):
    _name = "child.household.duty"
    _inherit = "child.property"
    _description = "Household Duty"
    res_field = "duty_ids"


class ProjectActivity(models.Model):
    _name = "child.project.activity"
    _inherit = "child.property"
    _description = "Project Activity"
    res_field = "project_activity_ids"


class SchoolSubject(models.Model):
    _name = "child.school.subject"
    _inherit = "child.property"
    _description = "Household Duty"
    res_field = "subject_ids"


class ChildHobby(models.Model):
    _name = "child.hobby"
    _inherit = "child.property"
    _description = "Child Hobby"
    res_field = "hobby_ids"


class ChristianActivity(models.Model):
    _name = "child.christian.activity"
    _inherit = "child.property"
    _description = "Child christian activity"
    res_field = "christian_activity_ids"


class PhysicalDisability(models.Model):
    _name = "child.physical.disability"
    _inherit = "child.property"
    _description = "Child physical disability"
    res_field = "physical_disability_ids"


class ChronicIllness(models.Model):
    _name = "child.chronic.illness"
    _inherit = "child.property"
    _description = "Child chronic illness"
    res_field = "chronic_illness_ids"


class FutureHope(models.Model):
    _name = "child.future.hope"
    _inherit = "child.property"
    _description = "Child future hope"
    res_model = "compassion.child.ble"
    res_field = "future_hope_ids"
