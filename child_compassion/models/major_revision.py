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


class MajorRevision(models.Model):
    _inherit = 'translatable.model'
    _name = 'compassion.major.revision'
    _description = 'Compassion Major Revision'

    name = fields.Selection([
        # Child major revision
        ('Birthdate', 'Birthdate'),
        ('Physical Disabilities', 'Physical Disabilities'),
        ('Chronic Illness', 'Chronic Illness'),
        ('First Name', 'First Name'),
        ('Formal Education Level', 'Formal Education Level'),
        ('Gender', 'Gender'),
        ('Last Name', 'Last Name'),
        ('Planned Completion Date', 'Planned Completion Date'),
        ('Preferred Name', 'Preferred Name'),
        ('Local Grade Level', 'Local Grade Level'),
        # Household major revision
        ('Is Natural Father Alive?', 'Natural Father Alive'),
        ('Is Natural Mother Alive?', 'Natural Mother Alive'),
        ('Primary Caregiver', 'Primary Caregiver'),
    ], required=True)
    old_value = fields.Char()
    child_id = fields.Many2one('compassion.child', ondelete='cascade', readonly=False)
    household_id = fields.Many2one('compassion.household', ondelete='cascade', readonly=False)

    @api.model
    def create(self, vals):
        major_field = super().create(vals)
        major_field.old_value = major_field.get_field_value()
        return major_field

    @api.model
    def get_field_mapping(self):
        return {
            'Birthdate': 'birthdate',
            'Physical Disabilities': 'physical_disability_ids.value',
            'Chronic Illness': 'chronic_illness_ids.value',
            'First Name': 'firstname',
            'Formal Education Level': 'formal_education',
            'Gender': 'gender',
            'Last Name': 'lastname',
            'Planned Completion Date': 'completion_date',
            'Preferred Name': 'preferred_name',
            'Is Natural Father Alive?': 'father_alive',
            'Is Natural Mother Alive?': 'mother_alive',
            'Primary Caregiver': 'primary_caregiver',
            'Local Grade Level': 'local_grade_level'
        }

    @api.model
    def get_child_field_mapping(self):
        return {
            'Birthdate': 'birthdate',
            'Physical Disabilities': 'physical_disability_ids.value',
            'Chronic Illness': 'chronic_illness_ids.value',
            'First Name': 'firstname',
            'Formal Education Level': 'formal_education',
            'Gender': 'gender',
            'Last Name': 'lastname',
            'Planned Completion Date': 'completion_date',
            'Preferred Name': 'preferred_name'
        }

    @api.multi
    def get_field_value(self):
        values = list()
        for revision in self:
            child_field_mapping = revision.get_child_field_mapping()
            child_res_object = revision.child_id
            if child_res_object and revision.name in child_field_mapping:
                values.extend(child_res_object.mapped(
                    child_field_mapping[revision.name]))
            else:
                field_mapping = revision.get_field_mapping()
                household_res_object = revision.household_id
                if household_res_object:
                    values.extend(household_res_object.mapped(
                        field_mapping[revision.name]))

        return u', '.join(values)
