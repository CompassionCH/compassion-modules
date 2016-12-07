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

    _sql_constraints = [('household_uniq', 'unique(household_id)',
                         'A Household with the same ID already exists.')]

    # Parents
    #########
    parents_together = fields.Selection('_get_yes_no')
    father_alive = fields.Selection('_get_yes_no')
    father_living_with_child = fields.Boolean()
    marital_status = fields.Char()
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
            household.nb_brothers = len(brothers) - 1 if self.env.context.get(
                'active_gender') == 'M' else len(brothers)
            household.nb_sisters = len(sisters) - 1 if self.env.context.get(
                'active_gender') == 'F' else len(sisters)

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

    @api.model
    def _get_yes_no(self):
        return [
            ('Yes', _('Yes')),
            ('No', _('No')),
            ('Unknown', _('Unknown')),
        ]

    @api.model
    def _get_jobs(self):
        return [
            ('Agriculture / Farmer', 'Farmer'),
            ('Baker', 'Baker'),
            ('Carpenter', 'Carpenter'),
            ('Church Worker / Project Worker', 'Project worker'),
            ('Construction Worker', 'Construction worker'),
            ('Cook', 'Cook'),
            ('Clothing Trade', 'Works in clothing trade'),
            ('Construction / Tradesman', 'Construction worker'),
            ('Day Labor / Different Jobs', 'Daily jobs'),
            ('Electrician', 'Electrician'),
            ('Factory Worker', 'Factory worker'),
            ('Farmer', 'Farmer'),
            ('Fish Seller', 'Fish seller'),
            ('Fisher', 'Fisher'),
            ('Food Vendor', 'Food vendor'),
            ('Gardener', 'Gardener'),
            ('Guard / Watchman', 'Guard'),
            ('Hairdresser', 'Hairdresser'),
            ('Health Care Worker', 'Health care worker'),
            ('Homemaker', 'Homemaker'),
            ('Janitor', 'Janitor'),
            ('Knitter / Weaver', 'Knitter'),
            ('Laundry Worker', 'Laundry worker'),
            ('Law Enforcement', 'Law enforcement'),
            ('Manicurist', 'Manicurist'),
            ('Mason / Bricklayer', 'Mason'),
            ('Mechanic', 'Mechanic'),
            ('Merchant / Seller', 'Merchant'),
            ('Nurse', 'Nurse'),
            ('Other', 'Other'),
            ('Painter', 'Painter'),
            ('Plumber', 'Plumber'),
            ('Security / Guard', 'Security guard'),
            ('Tailor / Seamstress', 'Tailor'),
            ('Teacher', 'Teacher'),
            ('Transportation / Driver', 'Driver'),
            ('Unknown', 'Unknown'),
            ('Waiter / Food Server', 'Food server'),
            ('Welder', 'Welder'),
            # TODO see if these values are only in test
            ('Agriculture/ Farmer', 'Farmer'),
            ('Church Worker', 'Project worker'),
            ('Clothing Trades', 'Works in clothing trade'),
            ('Construction/ Tradesman', 'Construction worker'),
            ('Day Labor/ Different Jobs', 'Daily jobs'),
            ('Domestic Service / Housekeeper', 'Housekeeper'),
            ('Food Services', 'Food vendor'),
            ('Laborer', 'Laborer'),
            ('Housewife', 'Housewife'),
            ('Merchant/ Seller', 'Merchant'),
            ('Security/ Guard', 'Security guard'),
            ('Sells In Market', 'Merchant'),
            ('Transportation/ Driver', 'Driver'),
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
                household.write(household_vals)
        return household_ids

    ##########################################################################
    #                             ORM METHODS                                #
    ##########################################################################
    @api.model
    def create(self, vals):
        res = self.search([('household_id', '=', vals.get('household_id'))])
        if res:
            res.write(vals)
        else:
            res = super(Household, self).create(vals)
        return res


class HouseholdMembers(models.Model):
    _name = 'compassion.household.member'
    _inherit = 'translatable.model'
    _description = 'Household Member'

    beneficiary_local_id = fields.Char()
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
    gender = fields.Char(size=1, compute='_compute_gender', store=True)
    male_role = fields.Boolean(compute='_compute_gender', store=True)
    female_role = fields.Boolean(compute='_compute_gender', store=True)
    other_role = fields.Boolean(compute='_compute_gender', store=True)

    def _get_roles(self):
        return self._get_male_roles() + self._get_female_roles() + \
               self._get_other_roles()

    @api.model
    def _get_male_roles(self):
        return [
            ('Father', 'Father'),
            ('Grandfather', 'Grandfather'),
            ('Uncle', 'Uncle'),
            ('Step Father', 'Step father'),
            ('Godfather', 'Godfather'),
            ('Brother', 'Brother'),
            ('Beneficiary - Male', 'Beneficiary - Male'),
        ]

    @api.model
    def _get_female_roles(self):
        return [
            ('Mother', 'Mother'),
            ('Grandmother', 'Grandmother'),
            ('Aunt', 'Aunt'),
            ('Step Mother', 'Step mother'),
            ('Godmother', 'Godmother'),
            ('Sister', 'Sister'),
            ('Beneficiary - Female', 'Beneficiary - Female'),
        ]

    @api.model
    def _get_other_roles(self):
        return [
            ('Foster parent', 'Foster parent'),
            ('Friend', 'Friend'),
            ('Other non-relative', 'Other non-relative'),
            ('Other relative', 'Other relative'),
        ]

    @api.depends('role')
    @api.multi
    def _compute_gender(self):
        for caregiver in self:
            if caregiver.role in dict(self._get_male_roles()).keys():
                caregiver.male_role = True
                caregiver.gender = 'M'
            elif caregiver.role in dict(self._get_female_roles()).keys():
                caregiver.female_role = True
                caregiver.gender = 'F'
            else:
                caregiver.other_role = True
                caregiver.gender = 'M'
