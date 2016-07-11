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


from openerp import api, models, fields, _

from ..mappings.household_mapping import HouseHoldMapping


class Household(models.Model):
    _name = 'compassion.household'
    _description = 'Household'
    _inherit = 'translatable.model'

    household_id = fields.Char(required=True)
    child_ids = fields.One2many(
        'compassion.child', 'household_id', 'Beneficiaries')
    name = fields.Char()
    number_beneficiaries = fields.Integer()
    revised_value_ids = fields.One2many(
        'compassion.major.revision', 'household_id', 'Major revisions',
        readonly=True
    )

    # Parents
    #########
    parents_together = fields.Selection('_get_yes_no')
    father_alive = fields.Selection('_get_yes_no')
    father_living_with_child = fields.Boolean()
    marital_status = fields.Selection([
        ('Married', _('are married')),
        ('Never Married', _('were never married')),
        ('Unknown', 'unknown'),
        ('Were Married, Now Divorced Or Permanently Separated',
         _('are divorced')),
        ('Were Married, Now Separated By Death', _('are separated by death')),
    ])
    mother_alive = fields.Selection('_get_yes_no')
    mother_living_with_child = fields.Boolean()
    youth_headed_household = fields.Boolean()
    primary_caregiver = fields.Char(compute='_compute_primary_caregiver')

    # Employment
    ############
    male_guardian_job_type = fields.Selection([
        ('Regularly Employed', 'Regular'),
        ('Sometimes Employed', 'Sometimes employed'),
        ('Not Employed', 'Not employed'),
    ])
    male_guardian_job = fields.Selection('_get_jobs')
    female_guardian_job_type = fields.Selection([
        ('Regularly Employed', 'Regular'),
        ('Sometimes Employed', 'Sometimes employed'),
        ('Not Employed', 'Not employed'),
    ])
    female_guardian_job = fields.Selection('_get_jobs')
    member_ids = fields.One2many(
        'compassion.household.member', 'household_id', 'Members')
    nb_brothers = fields.Integer(compute='_compute_siblings')
    nb_sisters = fields.Integer(compute='_compute_siblings')

    @api.multi
    def _compute_siblings(self):
        for household in self:
            brothers = household.member_ids.filtered(
                lambda member: member.role in (
                    'Brother', 'Beneficiary - Male'))
            sisters = household.member_ids.filtered(
                lambda member: member.role in (
                    'Sister', 'Beneficiary - Female'))
            household.nb_brothers = len(brothers) - 1
            household.nb_sisters = len(sisters) - 1

    @api.multi
    def _compute_primary_caregiver(self):
        for household in self:
            primary_caregiver = household.member_ids.filtered(
                'is_primary_caregiver')
            household.primary_caregiver = primary_caregiver.translate('role')

    @api.multi
    def get_male_guardian(self):
        self.ensure_one()
        caregiver = self.member_ids.filtered(
            lambda member: member.is_primary_caregiver and member.male_role)
        return caregiver.translate('role')

    @api.multi
    def get_female_guardian(self):
        self.ensure_one()
        caregiver = self.member_ids.filtered(
            lambda member: member.is_primary_caregiver and member.female_role)
        return caregiver.translate('role')

    @api.multi
    def get_caregivers(self):
        """ Returns valid names for caregivers. """
        self.ensure_one()
        caregivers = self.member_ids.filtered(
            lambda member: member.is_caregiver and member.role not in (
                'Brother', 'Sister', 'Beneficiary - Male',
                'Beneficiary - Female'
            ))
        return caregivers

    def _get_yes_no(self):
        return [
            ('Yes', _('Yes')),
            ('No', _('No')),
            ('Unknown', _('Unknown')),
        ]

    def _get_jobs(self):
        return [
            ('Agriculture/ Farmer', _('is a farmer')),
            ('Baker', _('is a baker')),
            ('Church Employee/ Project Worker', _('works for the local '
                                                  'church')),
            ('Clothing Trade', _('works in clothing trade')),
            ('Construction/ Tradesman', _('works in construction')),
            ('Day Labor/ Different Jobs', _('does daily jobs')),
            ('Health Care Worker', _('Health care worker')),
            ('Factory Worker', _('works in a factory')),
            ('Fisherman', _('is a fisherman')),
            ('Food Services', _('works in food services')),
            ('Janitor', _('is janitor')),
            ('Mechanic', _('is mechanic')),
            ('Merchant/ Seller', _('is merchant')),
            ('Other', 'other'),
            ('Security/ Guard', _('is a security guard')),
            ('Teacher', _('is a teacher')),
            ('Transportation/ Driver', _('is a driver')),
            ('Unknown', 'unknown'),
            ('Welder', _('is a welder')),
            # TODO see if these values are only in test
            ('Carpenter', _('is a carpenter')),
            ('Electrician', _('is an electrician')),
            ('Fish Seller', _('is a fish seller')),
            ('Gardener', _('is a gardener')),
            ('Construction Worker', _('is a construction worker')),
            ('Food Vendor', _('is a food vendor')),
            ('Guard / Watchman', _('is a guard')),
            ('Domestic Service / Housekeeper', ('is a domestic')),
        ]

    def process_commkit(self, commkit_data):
        """ Household Major Revision """
        household_ids = list()
        household_mapping = HouseHoldMapping(self.env)
        for household_data in commkit_data.get('BeneficiaryHouseholdList',
                                               [commkit_data]):
            household = self.search([
                ('household_id', '=', household_data.get('Household_ID'))])
            if household:
                household_ids.append(household.id)
                household_vals = household_mapping.get_vals_from_connect(
                    household_data)
                household._major_revision(household_vals)
        return household_ids

    def _major_revision(self, vals):
        self.ensure_one()
        self.write(vals)


class HouseholdMembers(models.Model):
    _name = 'compassion.household.member'
    _inherit = 'translatable.model'
    _description = 'Household Member'

    child_id = fields.Many2one(
        'compassion.child', 'Child'
    )
    household_id = fields.Many2one(
        'compassion.household', 'Household',
        required=True, ondelete='cascade')
    is_caregiver = fields.Boolean()
    is_primary_caregiver = fields.Boolean()
    name = fields.Char()
    role = fields.Selection('_get_roles')
    male_role = fields.Boolean(compute='_compute_gender', store=True)
    female_role = fields.Boolean(compute='_compute_gender', store=True)
    other_role = fields.Boolean(compute='_compute_gender', store=True)

    def _get_roles(self):
        return self._get_male_roles() + self._get_female_roles() + \
               self._get_other_roles()

    def _get_male_roles(self):
        return [
            ('Father', _('father')),
            ('Grandfather', _('grandfather')),
            ('Uncle', _('uncle')),
            ('Step Father', _('step father')),
            ('Godfather', _('godfather')),
            ('Brother', _('brother')),
            ('Beneficiary - Male', 'Beneficiary - Male'),
        ]

    def _get_female_roles(self):
        return [
            ('Mother', _('mother')),
            ('Grandmother', _('grandmother')),
            ('Aunt', _('aunt')),
            ('Step Mother', _('step mother')),
            ('Godmother', _('godmother')),
            ('Sister', _('sister')),
            ('Beneficiary - Female', 'Beneficiary - Female'),
        ]

    def _get_other_roles(self):
        return [
            ('Foster parent', _('foster parent')),
            ('Friend', _('friend')),
            ('Other non-relative', _('other non-relative')),
            ('Other relative', _('other relative')),
        ]

    @api.depends('role')
    @api.multi
    def _compute_gender(self):
        for caregiver in self:
            if caregiver.role in dict(self._get_male_roles()).keys():
                caregiver.male_role = True
            elif caregiver.role in dict(self._get_female_roles()).keys():
                caregiver.female_role = True
            else:
                caregiver.other_role = True

    @api.multi
    def contains(self, roles):
        """ True if the recordset contains given roles. """
        members = self.filtered(lambda member: member.role in roles)
        return len(members) == len(roles)

    @api.multi
    def remove(self, role):
        """ Returns the recordset without given role. """
        return self.filtered(lambda member: member.role != role)
