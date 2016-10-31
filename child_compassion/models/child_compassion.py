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

from openerp import models, fields, api, _
from datetime import datetime, timedelta

from ..wizards.child_description_fr import ChildDescriptionFr
from ..wizards.child_description_de import ChildDescriptionDe
from ..wizards.child_description_it import ChildDescriptionIt
from ..mappings.compassion_child_mapping import CompassionChildMapping

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.message_center_compassion.tools.onramp_connector import \
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
    exit_reason = fields.Char(compute='_compute_exit_reason')
    non_latin_name = fields.Char()

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
        ('Preschool', 'Preschool'),
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
        ('University Graduate', 'University Graduate'),
    ], readonly=True)
    local_grade_level = fields.Char(readonly=True)
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
        'child.disaster.impact', 'child_id', 'Child Disaster Impact'
    )

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
            ('N', _('Consigned')),
            ('I', _('On Internet')),
            ('P', _('Sponsored')),
            ('F', _('Departed')),
            ('R', _('Released')),
        ]

    def _set_available(self):
        for child in self:
            child.is_available = child.state in self._available_states()

    def _available_states(self):
        return ['N', 'I']

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
        child = self.search([('global_id', '=', global_id)])
        if child:
            child.write(vals)
        else:
            child = super(CompassionChild, self).create(vals)
        return child

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def details_answer(self, vals):
        """ Called when receiving the answer of GetDetails message. """
        self.ensure_one()
        self.write(vals)
        self.generate_descriptions()
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

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def get_infos(self):
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
        message_obj.create(message_vals)
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

    # Lifecycle methods
    ###################
    def depart(self):
        self.signal_workflow('release')

    def reinstatement(self):
        """ Called by Lifecycle Event. Hold and state of Child is
        handled by the Reinstatement Hold Notification. """
        self.delete_workflow()
        self.create_workflow()

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
    def child_consigned(self):
        """Called on child allocation."""
        self.write({'state': 'N', 'sponsor_id': False})
        # Cancel planned deletion
        jobs = self.env['queue.job'].search([
            ('name', '=', 'Job for deleting released children.'),
            ('func_string', 'like', self.ids),
            ('state', '=', 'enqueued')
        ])
        jobs.button_done()
        jobs.unlink()
        return True

    @api.multi
    def child_sponsored(self):
        for child in self:
            self.env['compassion.child.pictures'].create({
                'child_id': child.id,
                'image_url': child.image_url
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
        default_expiration = datetime.now() + timedelta(weeks=1)
        for child in other_children:
            postpone = fields.Datetime.from_string(child.hold_expiration) or \
                default_expiration
            session = ConnectorSession.from_env(other_children.env)
            unlink_children_job.delay(session, self._name, child.ids,
                                      eta=postpone)

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


##############################################################################
#                            CONNECTOR METHODS                               #
##############################################################################
@job(default_channel='root.child_compassion')
def unlink_children_job(session, model_name, message_ids):
    """Job for deleting released children."""
    children = session.env[model_name].browse(message_ids)
    children.unlink()
