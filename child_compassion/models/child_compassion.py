# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Cyril Sester
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.addons.advanced_translation.models.ir_advanced_translation \
    import setlocale
from datetime import datetime, date

from ..mappings.compassion_child_mapping import CompassionChildMapping
from .compassion_hold import HoldType

from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.message_center_compassion.tools.onramp_connector import \
    OnrampConnector

logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    """ A sponsored child """
    _name = 'compassion.child'
    _rec_name = 'local_id'
    _inherit = ['compassion.generic.child', 'mail.thread',
                'translatable.model']
    _description = "Sponsored Child"
    _order = 'local_id asc,date desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # General Information
    #####################
    local_id = fields.Char(track_visibility='onchange')
    code = fields.Char(help='Old child reference')
    compass_id = fields.Char('Compass ID', oldname='unique_id')
    estimated_birthdate = fields.Boolean(readonly=True)
    cognitive_age_group = fields.Char(readonly=True)
    cdsp_type = fields.Selection([
        ('Home Based', 'Home based'),
        ('Center Based', 'Center based'),
    ], track_visibility='onchange', readonly=True)
    last_review_date = fields.Date(track_visibility='onchange', readonly=True)
    last_photo_date = fields.Date()
    type = fields.Selection('_get_ctype', required=True, default='CDSP')
    date = fields.Date('Allocation date')
    completion_date = fields.Date(readonly=True)
    completion_date_change_reason = fields.Char(readonly=True)
    state = fields.Selection(
        '_get_child_states', readonly=True, required=True,
        track_visibility='onchange', default='N',)
    is_available = fields.Boolean(compute='_compute_available')
    sponsor_id = fields.Many2one(
        'res.partner', 'Sponsor', track_visibility='onchange', readonly=True)
    partner_id = fields.Many2one(
        'res.partner', related='sponsor_id'
    )
    sponsor_ref = fields.Char(
        'Sponsor reference', related='sponsor_id.ref')
    has_been_sponsored = fields.Boolean()
    exit_reason = fields.Char(compute='_compute_exit_reason')
    non_latin_name = fields.Char()
    birthday_dm = fields.Char(
        'Birthday', compute='_compute_birthday_month', store=True)
    birthday_month = fields.Selection(
        '_get_months', compute='_compute_birthday_month', store=True)

    # Hold Information
    ##################
    hold_id = fields.Many2one('compassion.hold', 'Hold', readonly=True)
    hold_type = fields.Selection(related='hold_id.type', store=True)
    hold_channel = fields.Selection(related='hold_id.channel', store=True)
    hold_owner = fields.Many2one(related='hold_id.primary_owner', store=True)
    hold_ambassador = fields.Many2one(related='hold_id.ambassador', store=True)
    hold_expiration = fields.Datetime(related='hold_id.expiration_date',
                                      string='Hold expiration', store=True)

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
        ('Preschool', 'preschool'),
        ('Primary', 'primary school'),
        ('Secondary', 'secondary school'),
        ('University Graduate', 'university'),
    ], readonly=True)
    local_grade_level = fields.Char(readonly=True)
    us_grade_level = fields.Char(readonly=True)
    academic_performance = fields.Selection([
        ('Above Average', 'Above average'),
        ('Average', 'Average'),
        ('Below Average', 'Below average'),
        ('Not Available', ''),
    ], readonly=True)
    vocational_training_type = fields.Selection([
        ('Agriculture', 'Agriculture'),
        ('Architecture / Drafting', 'Architecture'),
        ('Art / Design', 'Art / Design'),
        ('Automotive', 'Automotive'),
        ('Automotive / Mechanics', 'Automotive'),
        ('Business/Administrative', 'Business administration'),
        ('Business / Administration', 'Business administration'),
        ('Clothing Trades', 'Clothing trades'),
        ('Computer Technology', 'Computer technology'),
        ('Computer / Technology', 'Computer technology'),
        ('Construction/ Tradesman', 'Construction'),
        ('Construction / Tradesman', 'Construction'),
        ('Cooking / Food Service', 'Cooking and food service'),
        ('Cosmetology', 'Cosmetology'),
        ('Electrical/ Electronics', 'Electronics'),
        ('Electrical / Electronics', 'Electronics'),
        ('Graphic Arts', 'Graphic arts'),
        ('Hospitality / Hotel / Tourism', 'Hospitality, hotel and tourism'),
        ('Income-Generating Program at Project',
         'Income-generating program at project'),
        ('Industrial / Manufacturing / Fabrication',
         'Industrial / Manufacturing / Fabrication'),
        ('Manufacturing/ Fabrication', 'Manufacturing / Fabrication'),
        ('Manufacturing / Fabrication', 'Manufacturing / Fabrication'),
        ('Medical/ Health Services', 'Medical / Health services'),
        ('Medical / Health Services', 'Medical / Health services'),
        ('Not Enrolled', 'Not enrolled'),
        ('Not enrolled', 'Not enrolled'),
        ('Other', 'Other'),
        ('Para-Medical / Medical / Health Services',
         'Medical / Health services'),
        ('Telecommunication', 'Telecommunication'),
        ('Transportation', 'Transportation'),
        ('Transportation/ Driver', 'Driver'),
        ('Transportation / Driver', 'Driver'),
    ], readonly=True)
    university_year = fields.Integer(readonly=True)
    major_course_study = fields.Selection([
        ('Accounting', 'Accounting'),
        ('Agriculture', 'Agriculture'),
        ('Biology / Medicine', 'Biology / Medicine'),
        ('Business / Management / Commerce', 'Business management'),
        ('Community Development', 'Community development'),
        ('Computer Science / Information Technology', 'Computer science'),
        ('Criminology / Law Enforcement', 'Criminology'),
        ('Economics', 'Economics'),
        ('Education', 'Education'),
        ('Engineering', 'Engineering'),
        ('English', 'English'),
        ('Graphic Arts / Fine Arts', 'Graphic arts'),
        ('History', 'History'),
        ('Hospitality / Hotel Management', 'Hospitality / Hotel '
                                           'management'),
        ('Law', 'Law'),
        ('Mathematics', 'Mathematics'),
        ('Medical/ Health Services', 'Medical / Health services'),
        ('Medical / Health Services', 'Medical / Health services'),
        ('Nursing', 'Nursing'),
        ('Psychology', 'Psychology'),
        ('Sales and Marketing', 'Sales and marketing'),
        ('Science', 'Science'),
        ('Sociology / Social Science', 'Sociology'),
        ('Theology', 'Theology'),
        ('Tourism', 'Tourism'),
        ('Biology', 'Biology'),
        ('Social Science', 'Social Science'),
        ('Sociology', 'Sociology'),
        ('Hotel Management', 'Hotel Management'),
        ('Hospitality', 'Hospitality'),
        ('Fine Arts', 'Fine Arts'),
        ('Graphic Arts', 'Graphic Arts'),
        ('Law Enforcement', 'Law Enforcement'),
        ('Criminology', 'Criminology'),
        ('Information Technology', 'Information Technology'),
        ('Computer Science ', 'Computer Science'),
        ('Business', 'Business'),
        ('Management', 'Management'),
        ('Commerce', 'Commerce'),
        ('Medicine', 'Medicine'),
        ('Other', 'Other')
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

    # Case Studies
    ##############
    lifecycle_ids = fields.One2many(
        'compassion.child.ble', 'child_id', 'Lifecycle events', readonly=True)
    assessment_ids = fields.One2many(
        'compassion.child.cdpr', 'child_id', 'Assessments', readonly=True
    )
    note_ids = fields.One2many(
        'compassion.child.note', 'child_id', 'Notes', readonly=True
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
    child_disaster_impact_ids = fields.One2many(
        'child.disaster.impact', 'child_id', 'Child Disaster Impact',
        readonly=True
    )

    # Descriptions
    ##############
    desc_en = fields.Text('English description', readonly=True)

    # Just for migration
    delegated_comment = fields.Text()

    _sql_constraints = [
        ('compass_id', 'unique(compass_id)',
         'The child already exists in database.'),
        ('global_id', 'unique(global_id)',
         'The child already exists in database.')
    ]

    is_special_needs = fields.Boolean()
    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.model
    def _get_child_states(self):
        return [
            ('W', _('Waiting Hold')),
            ('N', _('Consigned')),
            ('I', _('On Internet')),
            ('P', _('Sponsored')),
            ('F', _('Departed')),
            ('R', _('Released')),
        ]

    def _compute_available(self):
        for child in self:
            child.is_available = child.state in self._available_states()

    @api.model
    def _available_states(self):
        return ['N', 'I']

    def _compute_exit_reason(self):
        for child in self:
            exit_details = child.lifecycle_ids.with_context(
                lang='en_US').filtered(
                lambda l: l.type in ('Planned Exit', 'Unplanned Exit'))
            if exit_details:
                child.exit_reason = exit_details[0].request_reason

    @api.model
    def _get_ctype(self):
        return [('CDSP', 'CDSP'), ('LDP', 'LDP')]

    @api.model
    def _get_months(self):
        return self.env['connect.month'].get_months_selection()[12:]

    @api.depends('birthdate')
    def _compute_birthday_month(self):
        with setlocale('en_US'):
            for child in self.filtered('birthdate'):
                birthday = fields.Date.from_string(child.birthdate)
                child.birthday_month = birthday.strftime('%B')
                child.birthday_dm = birthday.strftime('%m-%d')

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
        child = self.search([('global_id', '=', global_id)])
        if child:
            child.write(vals)
        else:
            child = super(CompassionChild, self).create(vals)
            # directly fetch picture to have it before get_infos
            child.update_child_pictures()
        return child

    @api.multi
    def unlink(self):
        holds = self.mapped('hold_id').filtered(
            lambda h: h.state == 'active' and
            h.type != HoldType.NO_MONEY_HOLD.value)
        res = super(CompassionChild, self).unlink()
        holds.release_hold()
        return res

    @api.multi
    @job(default_channel='root.child_compassion')
    @related_action('related_action_child_compassion')
    def unlink_job(self):
        """ Small wrapper to unlink only released children. """
        return self.filtered(lambda c: c.state == 'R').unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def details_answer(self, vals):
        """ Called when receiving the answer of GetDetails message. """
        self.ensure_one()
        self.write(vals)
        self.env['compassion.child.description'].create({'child_id': self.id})
        self.update_child_pictures()
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

    @api.model
    def new_kit(self, commkit_data):
        """ New child kit is received. """
        child_mapping = CompassionChildMapping(self.env)
        children = self
        for child_data in commkit_data.get('BeneficiaryResponseList',
                                           [commkit_data]):
            global_id = child_data.get('Beneficiary_GlobalID')
            child = self.search([('global_id', '=', global_id)])
            if child:
                children += child
                child.write(child_mapping.get_vals_from_connect(child_data))
        children.update_child_pictures()
        return children.ids

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def get_infos(self):
        """Get the most recent case study, basic informations, updates
           portrait picture and creates the project if it doesn't exist.
        """
        message_obj = self.env['gmc.message.pool']
        action_id = self.env.ref('child_compassion.beneficiaries_details').id
        for child in self:
            message_vals = {
                'action_id': action_id,
                'object_id': child.id,
                'child_id': child.id,
            }
            message = message_obj.create(message_vals)
            if message.state == 'failure' and not self.env.context.get(
                    'async_mode'):
                raise UserError(message.failure_reason)
        return True

    @api.multi
    def update_child_pictures(self):
        """
        Check if there is a new picture if all conditions are satisfied:
        - At least two pictures
        - Difference between two last pictures is at least 6 months
        - Last picture is no older than 6 months
        :return: True
        """
        res = True
        # Update child's pictures
        for child in self:
            res = child._get_last_pictures() and res
            pictures = child.pictures_ids
            if res and len(pictures) > 1:
                today = date.today()
                last_photo = fields.Date.from_string(pictures[1].date)
                new_photo = fields.Date.from_string(pictures[0].date)
                diff_pic = relativedelta(new_photo, last_photo)
                diff_today = relativedelta(today, new_photo)
                if (diff_pic.months > 6 or diff_pic.years > 0) and (
                        diff_today.months <= 6 and diff_today.years == 0):
                    child.new_photo()
        return res

    # Lifecycle methods
    ###################
    @api.multi
    def depart(self):
        self.signal_workflow('release')

    @api.multi
    def reinstatement(self):
        """ Called by Lifecycle Event. Hold and state of Child is
        handled by the Reinstatement Hold Notification. """
        self.delete_workflow()
        self.create_workflow()

    @api.multi
    def new_photo(self):
        """
        Hook for doing something when a new photo is attached to the child.
        """
        pass

    @api.multi
    def get_lifecycle_event(self):
        onramp = OnrampConnector()
        endpoint = 'beneficiaries/{}/kits/beneficiarylifecycleeventkit'
        lifecylcle_ids = list()
        for child in self:
            result = onramp.send_message(
                endpoint.format(child.global_id), 'GET')
            if 'BeneficiaryLifecycleEventList' in result.get('content', {}):
                lifecylcle_ids.extend(self.env[
                    'compassion.child.ble'].process_commkit(result['content']))
        return lifecylcle_ids

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def child_waiting_hold(self):
        """ Called on child creation. """
        self.write({'state': 'W', 'sponsor_id': False})
        # If hold was already set, put it back in ConsignmentHold type
        self.mapped('hold_id').write({
            'type': HoldType.CONSIGNMENT_HOLD.value
        })
        return True

    @api.multi
    def child_consigned(self):
        """Called on child allocation."""
        self.write({'state': 'N'})
        # Cancel planned deletion
        jobs = self.env['queue.job'].search([
            ('name', '=', 'Job for deleting released children.'),
            ('func_string', 'like', self.ids),
            ('state', '=', 'enqueued')
        ])
        jobs.button_done()
        jobs.unlink()
        self.with_context(async_mode=False).get_infos()
        return True

    @api.multi
    def child_sponsored(self):
        for child in self:
            self.env['compassion.child.pictures'].create({
                'child_id': child.id,
                'image_url': child.image_url
            })
            hold = child.hold_id
            if hold.type != HoldType.SUB_CHILD_HOLD.value:
                hold.write({
                    'type': HoldType.NO_MONEY_HOLD.value,
                    'expiration_date': hold.get_default_hold_expiration(
                        HoldType.NO_MONEY_HOLD)
                })
        return self.write({
            'state': 'P',
            'has_been_sponsored': True
        })

    @api.multi
    def child_released(self):
        """ Is called when a child is released to the global childpool. """
        self.write({
            'sponsor_id': False,
            'state': 'R'
        })

        sponsored_children = self.filtered('has_been_sponsored')
        other_children = self - sponsored_children
        other_children.get_lifecycle_event()

        # the children will be deleted when we reach their expiration date
        postpone = 60 * 60 * 24 * 7  # One week by default
        today = datetime.today()
        for child in other_children:
            if child.hold_expiration:
                expire = fields.Datetime.from_string(child.hold_expiration)
                postpone = (expire - today).total_seconds() + 60

            child.with_delay(eta=postpone).unlink_job()

        return True

    @api.multi
    def child_departed(self):
        """ Is called when a child is departed. """
        sponsored_children = self.filtered('has_been_sponsored')
        sponsored_children.write({
            'sponsor_id': False,
            'state': 'F'
        })
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    @api.multi
    def _get_last_pictures(self):
        self.ensure_one()

        pictures_obj = self.env['compassion.child.pictures']
        pictures = pictures_obj.create({
            'child_id': self.id,
            'image_url': self.image_url})
        if pictures:
            # Add a note in child
            self.message_post(_("The picture has been updated."),
                              _("Picture update"), message_type='comment')

        return pictures

    def _major_revision(self, vals):
        """ Private method when a major revision is received for a child.
            :param vals: Record values received from connect
        """
        self.ensure_one()
        self.write(vals)
        self.get_infos()
