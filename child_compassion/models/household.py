# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import models, fields, _


class Household(models.Model):
    _name = 'compassion.household'
    _description = 'Household'

    household_id = fields.Char(required=True)
    child_ids = fields.One2many(
        'compassion.child', 'household_id', 'Beneficiaries')
    name = fields.Char()

    # Parents
    #########
    parents_together = fields.Selection('_get_yes_no')
    father_alive = fields.Selection('_get_yes_no')
    father_living_with_child = fields.Boolean()
    marital_status = fields.Selection([
        ('Married', 'Married'),
        ('Never Married', 'Never Married'),
        ('Unknown', 'Unknown'),
        ('Were Married, Now Divorced Or Permanently Separated', 'Divorced'),
        ('Were Married, Now Separated By Death', 'Separated By Death'),
    ])
    mother_alive = fields.Selection('_get_yes_no')
    mother_living_with_child = fields.Boolean()
    youth_headed_household = fields.Boolean()

    # Employment
    ############
    male_guardian_job_type = fields.Selection([
        ('Regularly Employed', 'Regularly Employed'),
        ('Sometimes Employed', 'Sometimes Employed'),
        ('Not Employed', 'Not Employed'),
    ])
    male_guardian_job = fields.Selection('_get_jobs')
    female_guardian_job_type = fields.Selection([
        ('Regularly Employed', 'Regularly Employed'),
        ('Sometimes Employed', 'Sometimes Employed'),
        ('Not Employed', 'Not Employed'),
    ])
    female_guardian_job = fields.Selection('_get_jobs')
    member_ids = fields.One2many(
        'compassion.household.member', 'household_id', 'Members')

    def _get_yes_no(self):
        return [
            ('Yes', _('Yes')),
            ('No', _('No')),
            ('Unknown', _('Unknown')),
        ]

    def _get_jobs(self):
        return [
            ('Agriculture/ Farmer', _('Farmer')),
            ('Baker', _('Baker')),
            ('Church Employee/ Project Worker', _('Church Employee')),
            ('Clothing Trade', _('Clothing Trade')),
            ('Construction/ Tradesman', _('Construction')),
            ('Day Labor/ Different Jobs', _('Day Labor')),
            ('Factory Worker', _('Factory Worker')),
            ('Fisherman', _('Fisherman')),
            ('Food Services', _('Food Services')),
            ('Janitor', _('Janitor')),
            ('Mechanic', _('Mechanic')),
            ('Merchant/ Seller', _('Merchant')),
            ('Other', _('Other')),
            ('Security/ Guard', _('Security/ Guard')),
            ('Teacher', _('Teacher')),
            ('Transportation/ Driver', _('Driver')),
            ('Unknown', _('Unknown')),
            ('Welder', _('Welder')),
        ]


class HouseholdMembers(models.Model):
    _name = 'compassion.household.member'

    household_id = fields.Many2one(
        'compassion.household', 'Household', required=True, ondelete='cascade')
    name = fields.Char()
    role = fields.Selection('_get_roles')
    is_primary_caregiver = fields.Boolean()
    is_caregiver = fields.Boolean()

    def get_role_keys(self):
        return [
            role[0].lowers().replace(' ', '') for role in self._get_roles()
        ]

    def _get_roles(self):
        return [
            ('Aunt', _('Aunt')),
            ('Beneficiary - Female', _('Beneficiary - Female')),
            ('Beneficiary - Male', _('Beneficiary - Male')),
            ('Brother', _('Brother')),
            ('Father', _('Father')),
            ('Foster parent', _('Foster parent')),
            ('Friend', _('Friend')),
            ('Godfather', _('Godfather')),
            ('Godmother', _('Godmother')),
            ('Grandfather', _('Grandfather')),
            ('Grandmother', _('Grandmother')),
            ('Mother', _('Mother')),
            ('Other non-relative', _('Other non-relative')),
            ('Other relative', _('Other relative')),
            ('Sister', _('Sister')),
            ('Step Father', _('Step Father')),
            ('Step Mother', _('Step Mother')),
            ('Uncle', _('Uncle')),
    ]
