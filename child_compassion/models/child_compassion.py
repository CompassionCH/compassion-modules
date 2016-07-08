# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Cyril Sester
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
from datetime import datetime

from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from ..wizards.child_description_fr import ChildDescriptionFr
from ..wizards.child_description_de import ChildDescriptionDe
from ..wizards.child_description_it import ChildDescriptionIt
from ..mappings.compassion_child_mapping import CompassionChildMapping

logger = logging.getLogger(__name__)


class GenericChild(models.AbstractModel):
    """ Generic information of children shared by subclasses:
        - compassion.child : sponsored children
        - compassion.global.child : available children in global pool
    """
    _name = 'compassion.generic.child'

    # General Information
    #####################
    global_id = fields.Char('Global ID', required=True, readonly=True)
    correspondence_language_id = fields.Many2one(
        'res.lang.compassion', 'Correspondence language')
    local_id = fields.Char(
        'Local ID', size=11, required=True, help='Child reference',
        readonly=True)
    project_id = fields.Many2one('compassion.project', 'Project')
    field_office_id = fields.Many2one(
        'compassion.field.office', 'Field office',
        related='project_id.field_office_id')
    name = fields.Char()
    firstname = fields.Char()
    lastname = fields.Char()
    preferred_name = fields.Char()
    gender = fields.Selection([('F', 'Female'), ('M', 'Male')], readonly=True)
    birthdate = fields.Date(readonly=True)
    age = fields.Integer(readonly=True)
    is_orphan = fields.Boolean(readonly=True)
    beneficiary_state = fields.Selection([
        ("Available", "Available"),
        ("Change Commitment Hold", "Change Commitment Hold"),
        ("Consignment Hold", "Consignment Hold"),
        ("Delinquent Mass Cancel Hold", "Delinquent Mass Cancel Hold"),
        ("E-Commerce Hold", "E-Commerce Hold"),
        ("Inactive", "Inactive"),
        ("Ineligible", "Ineligible"),
        ("No Money Hold", "No Money Hold"),
        ("Reinstatement Hold", "Reinstatement Hold"),
        ("Reservation Hold", "Reservation Hold"),
        ("Sponsor Cancel Hold", "Sponsor Cancel Hold"),
        ("Sponsored", "Sponsored"),
        ("Sub Child Hold", "Sub Child Hold"),
    ], readonly=True)
    sponsorship_status = fields.Selection([
        ('Sponsored', 'Sponsored'),
        ('Unsponsored', 'Unsponsored'),
    ], readonly=True)
    unsponsored_since = fields.Date(readonly=True)


class GlobalChild(models.TransientModel):
    """ Available child in the global childpool
    """
    _name = 'compassion.global.child'
    _inherit = 'compassion.generic.child'
    _description = 'Global Child'

    portrait = fields.Binary()
    fullshot = fields.Binary()
    image_url = fields.Char()
    color = fields.Integer(compute='_compute_color')
    is_area_hiv_affected = fields.Boolean()
    is_special_needs = fields.Boolean()
    field_office_id = fields.Many2one(store=True)
    search_view_id = fields.Many2one(
        'compassion.childpool.search'
    )
    priority_score = fields.Float(help='How fast the child should be '
                                       'sponsored')
    correspondent_score = fields.Float(help='Score based on how long the '
                                            'child is waiting')
    holding_global_partner_id = fields.Many2one(
        'compassion.global.partner', 'Holding global partner'
    )
    waiting_days = fields.Integer()
    hold_expiration_date = fields.Datetime()
    source_code = fields.Char(
        'origin of the hold'
    )

    @api.multi
    def _compute_color(self):
        for child in self:
            child.color = 6 if child.gender == 'M' else 9


class CompassionChild(models.Model):
    """ A sponsored child """
    _name = 'compassion.child'
    _rec_name = 'local_id'
    _inherit = ['compassion.generic.child', 'mail.thread',
                'translatable.model']
    _description = "Sponsored Child"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # General Information
    #####################
    local_id = fields.Char(track_visibility=True)
    code = fields.Char(help='Old child reference')
    compass_id = fields.Char('Compass ID', oldname='unique_id')
    estimated_birthdate = fields.Boolean(readonly=True)
    cognitive_age_group = fields.Selection([
        ('0-2', '0-2'),
        ('3-5', '3-5'),
        ('6-8', '6-8'),
        ('9-11', '9-11'),
        ('12-14', '12-14'),
        ('15-18', '15-18'),
        ('19+', '19+'),
    ], readonly=True)
    cdsp_type = fields.Selection([
        ('Home based', 'Home based'),
        ('Center based', 'Center based'),
    ], track_visibility='onchange', readonly=True)
    last_review_date = fields.Date(track_visibility='onchange', readonly=True)
    type = fields.Selection(
        [('CDSP', 'CDSP'), ('LDP', 'LDP')], required=True, default='CDSP')
    date = fields.Date('Allocation date')
    completion_date = fields.Date(readonly=True)
    completion_date_change_reason = fields.Char(readonly=True)
    state = fields.Selection(
        '_get_child_states', readonly=True, required=True,
        track_visibility='onchange', default='N')
    is_available = fields.Boolean(compute='_set_available')
    sponsor_id = fields.Many2one(
        'res.partner', 'Sponsor', track_visibility='onchange', readonly=True)
    sponsor_ref = fields.Char(
        'Sponsor reference', related='sponsor_id.ref')
    has_been_sponsored = fields.Boolean()
    hold_id = fields.Many2one('compassion.hold', 'Hold', readonly=True)
    active = fields.Boolean(default=True)
    exit_reason = fields.Char(compute='_compute_exit_reason')
    non_latin_name = fields.Char()
    # Beneficiary Favorites
    #######################
    hobby_ids = fields.Many2many('child.hobby', string='Hobbies',
                                 readonly=True)
    duty_ids = fields.Many2many(
        'child.household.duty', string='Household duties', readonly=True)
    activity_ids = fields.Many2many(
        'child.project.activity', string='Project activities', readonly=True)
    subject_ids = fields.Many2many(
        'child.school.subject', string='School subjects', readonly=True)

    # Education information
    #######################
    education_level = fields.Selection([
        ('Not Enrolled', 'Not Enrolled'),
        ('Preschool', 'Preschool'),
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
        ('University Graduate', 'University Graduate'),
    ], readonly=True)
    local_grade_level = fields.Selection([
        ('Preschool 1', 'Preschool 1'),
        ('Preschool 2', 'Preschool 2'),
        ('Kinder 1', 'Kinder 1'),
        ('Kinder 2', 'Kinder 2'),
        ('Kinder 3', 'Kinder 3'),
        ('Primary 1', 'Primary 1'),
        ('Primary 2', 'Primary 2'),
        ('Primary 3', 'Primary 3'),
        ('Primary 4', 'Primary 4'),
        ('Primary 5', 'Primary 5'),
        ('Primary 6', 'Primary 6'),
        ('Middle 1', 'Middle 1'),
        ('Middle 2', 'Middle 2'),
        ('Middle 3', 'Middle 3'),
        ('High school 1', 'High school 1'),
        ('High school 2', 'High school 2'),
        ('High school 3', 'High school 3'),
        ('Not Enrolled', 'Not Enrolled'),
    ], readonly=True)
    us_grade_level = fields.Selection([
        ('P', 'P'),
        ('K', 'K'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
        ('13', '13'),
        ('14', '14'),
        ('PK', 'PK'),
    ], readonly=True)
    academic_performance = fields.Selection([
        ('Above Average', _('above average')),
        ('Average', _('average')),
        ('Below Average', _('below average')),
    ], readonly=True)
    vocational_training_type = fields.Selection([
        ('Agriculture', _('agriculture')),
        ('Automotive', _('automotive')),
        ('Business/Administrative', _('business administration')),
        ('Clothing Trades', _('clothing trades')),
        ('Computer Technology', _('computer technology')),
        ('Construction/ Tradesman', _('construction')),
        ('Cooking / Food Service', _('cooking and food service')),
        ('Cosmetology', _('cosmetology')),
        ('Electrical/ Electronics', _('electronics')),
        ('Graphic Arts', _('graphic arts')),
        ('Income-Generating Program at Project',
         'Income-Generating Program at Project'),
        ('Manufacturing/ Fabrication', 'Manufacturing/ Fabrication'),
        ('Medical/ Health Services', 'Medical/ Health Services'),
        ('Not Enrolled', 'Not Enrolled'),
        ('Other', 'Other'),
        ('Telecommunication', _('telecommunication')),
        ('Transportation', _('transportation')),
        ('Transportation/ Driver', _('driver')),
    ], readonly=True)
    university_year = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
    ], readonly=True)
    major_course_study = fields.Selection([
        ('Accounting', _('accounting')),
        ('Agriculture', _('agriculture')),
        ('Biology / Medicine', _('biology/medicine')),
        ('Business / Management / Commerce', _('business management')),
        ('Community Development', _('community development')),
        ('Computer Science / Information Technology', _('computer science')),
        ('Criminology / Law Enforcement', _('criminology')),
        ('Economics', _('economics')),
        ('Education', _('education')),
        ('Engineering', _('engineering')),
        ('English', _('english')),
        ('Graphic Arts / Fine Arts', _('graphic arts')),
        ('History', _('history')),
        ('Hospitality / Hotel Management', _('hospitality / hotel '
                                             'management')),
        ('Law', _('law')),
        ('Mathematics', _('mathematics')),
        ('Nursing', _('nursing')),
        ('Other', 'Other'),
        ('Psychology', _('Psychology')),
        ('Sales and Marketing', _('sales and marketing')),
        ('Science', _('science')),
        ('Sociology / Social Science', _('sociology')),
        ('Theology', _('theology')),
        ('Tourism', _('tourism')),
    ], readonly=True)
    not_enrolled_reason = fields.Char(readonly=True)

    # Spiritual information
    #######################
    christian_activity_ids = fields.Many2many(
        'child.christian.activity', string='Christian activities',
        readonly=True)

    # Medical information
    #####################
    weight = fields.Char(readonly=True)
    height = fields.Char(readonly=True)
    physical_disability_ids = fields.Many2many(
        'child.physical.disability', string='Physical disabilities',
        readonly=True
    )
    chronic_illness_ids = fields.Many2many(
        'child.chronic.illness', string='Chronic illnesses', readonly=True
    )

    # Delegation
    ############
    delegated_to = fields.Many2one('res.partner', 'Delegated to')
    delegated_comment = fields.Text('Delegated comment')
    date_delegation = fields.Date()
    date_end_delegation = fields.Date('Delegated until')

    # Case Studies
    ##############
    lifecycle_ids = fields.One2many(
        'compassion.child.ble', 'child_id', 'Lifecycle events', readonly=True)
    assessment_ids = fields.One2many(
        'compassion.child.cdpr', 'child_id', 'Assessments', readonly=True
    )
    revised_value_ids = fields.One2many(
        'compassion.major.revision', 'child_id', 'Major revisions',
        readonly=True
    )
    pictures_ids = fields.One2many(
        'compassion.child.pictures', 'child_id', 'Child pictures',
        track_visibility='onchange', readonly=True)
    household_id = fields.Many2one('compassion.household', 'Household',
                                   readonly=True)
    portrait = fields.Binary(related='pictures_ids.headshot')
    fullshot = fields.Binary(related='pictures_ids.fullshot')

    # Descriptions
    ##############
    desc_en = fields.Text('English description', readonly=True)
    desc_fr = fields.Text('French description', readonly=True)
    desc_de = fields.Text('German description', readonly=True)
    desc_it = fields.Text('Italian description', readonly=True)

    _sql_constraints = [
        ('compass_id', 'unique(compass_id)',
         _('The child already exists in database.')),
        ('global_id', 'unique(global_id)',
         _('The child already exists in database.'))
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.one
    @api.depends('local_id')
    def _set_project(self):
        if self.local_id:
            project = self.env['compassion.project'].search(
                [('icp_id', '=', self.local_id[:5])], limit=1)
            if not project:
                project = self.env['compassion.project'].create({
                    'icp_id': self.local_id[:5],
                    'name': self.local_id[:5],
                })
            self.project_id = project.id

    def _get_child_states(self):
        return [
            ('N', _('Available')),
            ('D', _('Delegated')),
            ('I', _('On Internet')),
            ('Z', _('Reinstated')),
            ('P', _('Sponsored')),
            ('F', _('Departed')),
        ]

    def _set_available(self):
        for child in self:
            child.is_available = child.state in self._available_states()

    def _available_states(self):
        return ['N', 'D', 'Z']

    def _compute_exit_reason(self):
        for child in self:
            exit_details = child.lifecycle_ids.with_context(
                lang='en_US').filtered(
                lambda l: l.type in ('Planned Exit', 'Unplanned Exit'))
            if exit_details:
                child.exit_reason = exit_details[0].request_reason

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """
        If child with global_id already exists, update it instead of creating
        a new one.
        """
        global_id = vals.get('global_id')
        child = False
        if global_id:
            child = self.search([
                ('global_id', '=', global_id),
                ('active', '=', False)
            ])
            if child:
                vals['active'] = True
                child.write(vals)
        if not child:
            child = super(CompassionChild, self).create(vals)
        child.get_infos(async_mode=True)
        return child

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def update_delegate(self):
        """Called by CRON to update delegated children.
        :param Recordset self: empty Recordset
        """
        children = self.search([('state', 'not in', ['F', 'P'])])
        children_to_delegate = self.copy()
        children_to_undelegate = list()

        for child in children:
            if child.date_delegation:
                if datetime.strptime(child.date_delegation, DF) \
                   <= datetime.today() and child.is_available:
                    children_to_delegate |= child

                if child.date_end_delegation and \
                   datetime.strptime(child.date_end_delegation, DF) <= \
                   datetime.today():
                    children_to_undelegate.append(child.id)

        children_to_delegate.write({'state': 'D'})

        self.env['undelegate.child.wizard'].with_context(
            active_ids=children_to_undelegate).undelegate()

        return True

    def details_answer(self, vals):
        """ Called when receiving the answer of GetDetails message. """
        self.ensure_one()
        self.write(vals)
        self.generate_descriptions()
        return True

    @api.model
    def major_revision(self, commkit_data):
        """ Called when a MajorRevision Kit is received. """
        child_ids = list()
        child_mapping = CompassionChildMapping(self.env)
        for child_data in commkit_data.get('BeneficiaryMajorRevisionList',
                                           [commkit_data]):
            global_id = child_data.get('Beneficiary_GlobalID')
            child = self.search([('global_id', '=', global_id)])
            if child:
                child_ids.append(child.id)
                child._major_revision(child_mapping.get_vals_from_connect(
                    child_data))
        return child_ids

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def get_infos(self, context=None, async_mode=False):
        """Get the most recent case study, basic informations, updates
           portrait picture and creates the project if it doesn't exist.
        """
        message_obj = self.env['gmc.message.pool']
        action_id = self.env.ref(
            'child_compassion.beneficiaries_details').id

        message_vals = {
            'action_id': action_id,
            'object_id': self.id,
            'child_id': self.id,
        }
        message_obj.with_context(async_mode=async_mode).create(message_vals)
        return True

    @api.multi
    def update_child_pictures(self):
        res = True
        # Update child's pictures
        for child in self:
            res = child._get_last_pictures() and res
        return res

    @api.multi
    def generate_descriptions(self):
        self.ensure_one()
        self.desc_fr = ChildDescriptionFr.gen_fr_translation(
            self.with_context(lang='fr_CH'))
        self.desc_de = ChildDescriptionDe.gen_de_translation(
            self.with_context(lang='de_DE'))
        self.desc_it = ChildDescriptionIt.gen_it_translation(
            self.with_context(lang='it_IT'))

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.one
    def child_available(self):
        """Called on creation of workflow. Determine the state of
        allocated child.
        """
        state = 'N'
        if self.has_been_sponsored:
            if self.state == 'F':
                # Child reinstatement
                state = 'Z'
                # TODO The child should be on reinstatement hold
                # Convert the hold to have time to propose it on the
                # previous sponsor
        if self.sponsor_id:
            # Child is already sponsored
            state = 'P'
        else:
            # Child has lost his sponsor. We inactivate it to release it
            # to the global child pool.
            if not self.hold_id:
                state = 'F'
                self.active = False
        self.state = state
        return True

    @api.multi
    def child_sponsored(self):
        self.write({
            'state': 'P',
            'has_been_sponsored': True})
        return True

    @api.multi
    def child_departed(self):
        """ Is called when a child changes his status to 'F'. """
        self.write({'sponsor_id': False})
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_basic_informations(self):
        """ Retrieves basic information from Get Child Information service.
        """
        return True

    def _get_last_pictures(self):
        self.ensure_one()
        pictures_obj = self.env['compassion.child.pictures']
        pictures = pictures_obj.create({'child_id': self.id})
        if pictures:
            # Add a note in child
            self.message_post(
                "The picture has been updated.",
                "Picture update", 'comment')

        return pictures

    def _major_revision(self, vals):
        """ Private method when a major revision is received for a child.
            :param vals: Record values received from connect
        """
        self.ensure_one()
        self.write(vals)
