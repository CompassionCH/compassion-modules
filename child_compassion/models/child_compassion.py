# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Cyril Sester
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging

from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime

from ..wizards.child_description_fr import ChildDescriptionFr

logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    """ A sponsored child """
    _name = 'compassion.child'
    _rec_name = 'local_id'
    _inherit = 'mail.thread'
    _description = "Child"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # General Information
    #####################
    compass_id = fields.Char('Compass ID', oldname='unique_id')
    global_id = fields.Char('Global ID')
    local_id = fields.Char(
        'Local ID', size=10, required=True, track_visibility='onchange',
        oldname='local_id', help=_('Child reference'))
    name = fields.Char()
    firstname = fields.Char(track_visibility='onchange')
    lastname = fields.Char(track_visibility='onchange')
    preferred_name = fields.Char()
    gender = fields.Selection([('F', 'Female'), ('M', 'Male')])
    birthdate = fields.Date(track_visibility='onchange')
    estimated_birthdate = fields.Boolean()
    cognitive_age_group = fields.Selection([
        ('0-2', '0-2'),
        ('3-5', '3-5'),
        ('6-8', '6-8'),
        ('9-11', '9-11'),
        ('12-14', '12-14'),
        ('15-18', '15-18'),
        ('19+', '19+'),
    ])
    is_orphan = fields.Boolean(track_visibility='onchange')
    beneficiary_status = fields.Selection([
        ('Draft', 'Draft'),
        ('Active', 'Active'),
    ])
    sponsorship_status = fields.Selection([
        ('Sponsored', 'Sponsored'),
        ('Unsponsored', 'Unsponsored'),
    ])
    cdsp_type = fields.Selection([
        ('Home based', 'Home based'),
        ('Center based', 'Center based'),
    ], track_visibility='onchange')
    last_review_date = fields.Date()
    project_id = fields.Many2one(
        'compassion.project', 'Project', store=True, compute='_set_project')
    type = fields.Selection(
        [('CDSP', 'CDSP'), ('LDP', 'LDP')], required=True, default='CDSP')
    date = fields.Date('Allocation date')
    completion_date = fields.Date(track_visibility='onchange')
    completion_date_change_reason = fields.Char()
    unsponsored_since = fields.Date()
    state = fields.Selection(
        '_get_child_states', readonly=True, required=True,
        track_visibility='onchange', default='N')
    is_available = fields.Boolean(compute='_set_available')
    sponsor_id = fields.Many2one(
        'res.partner', 'Sponsor', readonly=True, track_visibility='onchange')
    sponsor_ref = fields.Char(
        'Sponsor reference', related='sponsor_id.ref')
    has_been_sponsored = fields.Boolean()

    # Beneficiary Favorites
    #######################
    hobby_ids = fields.Many2many('child.hobby', string='Hobbies')
    duty_ids = fields.Many2many(
        'child.household.duty', string='Household duties')
    activity_ids = fields.Many2many(
        'child.project.activity', string='Project activities')
    subject_ids = fields.Many2many(
        'child.school.subject', string='School subjects')

    # Education information
    #######################
    education_level = fields.Selection([
        ('Not Enrolled', 'Not Enrolled'),
        ('Preschool', 'Preschool'),
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
        ('University Graduate', 'University Graduate'),
    ])
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
    ])
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
    ])
    academic_performance = fields.Selection([
        ('Above Average', 'Above Average'),
        ('Average', 'Average'),
        ('Below Average', 'Below Average'),
    ])
    vocational_training_type = fields.Selection([
        ('Agriculture', 'Agriculture'),
        ('Automotive', 'Automotive'),
        ('Business/Administrative', 'Business/Administrative'),
        ('Clothing Trades', 'Clothing Trades'),
        ('Computer Technology', 'Computer Technology'),
        ('Construction/ Tradesman', 'Construction/ Tradesman'),
        ('Cooking / Food Service', 'Cooking / Food Service'),
        ('Cosmetology', 'Cosmetology'),
        ('Electrical/ Electronics', 'Electrical/ Electronics'),
        ('Graphic Arts', 'Graphic Arts'),
        ('Income-Generating Program at Project',
         'Income-Generating Program at Project'),
        ('Manufacturing/ Fabrication', 'Manufacturing/ Fabrication'),
        ('Medical/ Health Services', 'Medical/ Health Services'),
        ('Not enrolled', 'Not enrolled'),
        ('Other', 'Other'),
        ('Telecommunication', 'Telecommunication'),
        ('Transportation', 'Transportation'),
        ('Transportation/ Driver', 'Transportation/ Driver'),
    ])
    university_year = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),

    ])
    major_course_study = fields.Selection([
        ('Accounting', 'Accounting'),
        ('Agriculture', 'Agriculture'),
        ('Biology / Medicine', 'Biology / Medicine'),
        ('Business / Management / Commerce',
         'Business / Management / Commerce'),
        ('Community Development', 'Community Development'),
        ('Computer Science / Information Technology',
         'Computer Science / Information Technology'),
        ('Criminology / Law Enforcement', 'Criminology / Law Enforcement'),
        ('Economics', 'Economics'),
        ('Education', 'Education'),
        ('Engineering', 'Engineering'),
        ('English', 'English'),
        ('Graphic Arts / Fine Arts', 'Graphic Arts / Fine Arts'),
        ('History', 'History'),
        ('Hospitality / Hotel Management', 'Hospitality / Hotel Management'),
        ('Law', 'Law'),
        ('Mathematics', 'Mathematics'),
        ('Nursing', 'Nursing'),
        ('Other', 'Other'),
        ('Psychology', 'Psychology'),
        ('Sales and Marketing', 'Sales and Marketing'),
        ('Science', 'Science'),
        ('Sociology / Social Science', 'Sociology / Social Science'),
        ('Theology', 'Theology'),
        ('Tourism', 'Tourism'),
    ])
    not_enrolled_reason = fields.Char()

    # Spiritual information
    #######################
    christian_activity_ids = fields.Many2many(
        'child.christian.activity', string='Christian activities')

    # Medical information
    #####################
    weight = fields.Char()
    height = fields.Char()
    physical_disability_ids = fields.Many2many(
        'child.physical.disability', string='Physical disabilities'
    )
    chronic_illness_ids = fields.Many2many(
        'child.chronic.illness', string='Chronic illnesses'
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
        'compassion.child.ble', 'child_id', 'Lifecycle events')
    assessment_ids = fields.One2many(
        'compassion.child.cdpr', 'child_id', 'Assessments'
    )
    pictures_ids = fields.One2many(
        'compassion.child.pictures', 'child_id', 'Child pictures',
        track_visibility='onchange')
    household_id = fields.Many2one('compassion.household', 'Household')
    portrait = fields.Binary(related='pictures_ids.headshot')
    fullshot = fields.Binary(related='pictures_ids.fullshot')

    # Descriptions
    ##############
    desc_en = fields.Text('English description')
    desc_fr = fields.Text('French description')
    desc_de = fields.Text('German description')
    desc_it = fields.Text('Italian description')

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
            ('R', _('Waiting new sponsor')),
            ('F', _('Departed')),
            ('X', _('Deallocated'))
        ]

    def _set_available(self):
        for child in self:
            child.is_available = child.state in self._available_states()

    def _available_states(self):
        return ['N', 'D', 'Z', 'R']

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def update_delegate(self):
        """Called by CRON to update delegated children.
        :param Recordset self: empty Recordset
        """
        children = self.search([('state', 'not in', ['F', 'X', 'P'])])
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

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def get_infos(self):
        """Get the most recent case study, basic informations, updates
           portrait picture and creates the project if it doesn't exist.
        """
        # TODO Implement with new service
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
        # TODO Add other languages
        self.ensure_one()
        self.desc_fr = ChildDescriptionFr.gen_fr_translation(
            self.with_context(lang='fr_CH'))

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
            else:
                # Child is waiting a new sponsor
                state = 'R'
        if self.sponsor_id:
            # Child is already sponsored
            state = 'P'
        self.state = state
        return True

    @api.multi
    def child_sponsored(self):
        self.write({
            'state': 'P',
            'has_been_sponsored': True})
        return True

    @api.one
    def child_departed(self):
        """ Is called when a child changes his status to 'F' or 'X'."""
        if self.state == 'F':
            self.sponsor_id = False
            self.get_exit_details()
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
