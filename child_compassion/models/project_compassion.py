# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Kevin Cristi, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
from openerp import models, fields, api, _

import sys

from ..wizards.project_description_fr import ProjectDescriptionFr
from ..wizards.project_description_de import ProjectDescriptionDe
from ..wizards.project_description_it import ProjectDescriptionIt

logger = logging.getLogger(__name__)


class CompassionProject(models.Model):
    """ A compassion project """
    _name = 'compassion.project'
    _rec_name = 'icp_id'
    _inherit = ['mail.thread', 'translatable.model']

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # General Information
    #####################
    icp_id = fields.Char(required=True, oldname='code', readonly=True)
    name = fields.Char()
    child_center_original_name = fields.Char(readonly=True)
    local_church_name = fields.Char(readonly=True)
    local_church_original_name = fields.Char(readonly=True)
    website = fields.Char(readonly=True)
    social_media_site = fields.Char(readonly=True)
    involvement_ids = fields.Many2many(
        'icp.involvement', string='Involvement', readonly=True)
    available_for_visits = fields.Boolean(readonly=True)
    nb_csp_kids = fields.Integer('CSP kids count', readonly=True)
    nb_cdsp_kids = fields.Integer('CDSP kids count', readonly=True)
    last_update_date = fields.Date('Last update', readonly=True)
    interested_partner_ids = fields.Many2many(
        'compassion.global.partner',
        string='GP interested with a church engagement',
        readonly=True)

    _sql_constraints = [
        ('icp_id_uniq', 'unique(icp_id)',
         'The ICP Id must be unique.'),
    ]

    # Location information
    ######################
    country = fields.Char(readonly=True)
    country_id = fields.Many2one(
        'res.country', 'Country', related='field_office_id.country_id',
        readonly=True)
    street = fields.Char(readonly=True)
    city = fields.Char(readonly=True)
    state_province = fields.Char(readonly=True)
    zip_code = fields.Char(readonly=True)
    gps_latitude = fields.Float(readonly=True)
    gps_longitude = fields.Float(readonly=True)
    cluster = fields.Char(readonly=True)
    territory = fields.Char(readonly=True)
    field_office_id = fields.Many2one(
        'compassion.field.office', 'Field Office',
        compute='_compute_field_office', store=True)

    # Church information
    ####################
    church_foundation_date = fields.Date(readonly=True)
    church_denomination = fields.Char(readonly=True)
    international_affiliation = fields.Char(readonly=True)
    ministry_ids = fields.Many2many(
        'icp.church.ministry', string='Church ministries', readonly=True
    )
    preferred_lang_id = fields.Many2one(
        'res.lang.compassion', 'Church preferred language', readonly=True)
    number_church_members = fields.Integer(readonly=True)
    weekly_child_attendance = fields.Integer(readonly=True)
    implemented_program_ids = fields.Many2many(
        'icp.program', string='Programs implemented', readonly=True
    )
    interested_program_ids = fields.Many2many(
        'icp.program', string='Programs of interest', readonly=True
    )

    # Church infrastructure information
    ###################################
    church_building_size = fields.Float(
        help='Unit is square meters', readonly=True)
    church_ownership = fields.Selection([
        ('Rented', 'Rented'),
        ('Owned', 'Owned'),
    ], readonly=True)
    facility_ids = fields.Many2many(
        'icp.church.facility', string='Church facilities', readonly=True
    )
    nb_staff_computers = fields.Char(size=2, readonly=True)
    nb_child_computers = fields.Char(size=2, readonly=True)
    nb_classrooms = fields.Char(size=2, readonly=True)
    nb_latrines = fields.Char(size=2, readonly=True)
    church_internet_access = fields.Selection([
        ('No', 'No'),
        ('Yes, onsite through one or more computers ', 'Onsite'),
        ('Yes, but offsite', 'Offsite'),

    ], readonly=True)
    mobile_device_ids = fields.Many2many(
        'icp.mobile.device', string='Mobile devices', readonly=True
    )
    utility_ids = fields.Many2many(
        'icp.church.utility', string='Church utilities', readonly=True
    )
    electrical_power = fields.Selection([
        ('Not Available', 'Not Available'),
        ('Available Sometimes', 'Available Sometimes'),
        ('Available Most of the Time', 'Available Most of the Time'),
    ], readonly=True)

    # ICP Activities
    ################
    spiritual_activity_babies_ids = fields.Many2many(
        'icp.spiritual.activity', 'icp_spiritual_baby_act',
        string='Spiritual activities (0-5)', readonly=True
    )
    spiritual_activity_kids_ids = fields.Many2many(
        'icp.spiritual.activity', 'icp_spiritual_kid_act',
        string='Spiritual activities (6-11)', readonly=True
    )
    spiritual_activity_ados_ids = fields.Many2many(
        'icp.spiritual.activity', 'icp_spiritual_ado_act',
        string='Spiritual activities (12+)', readonly=True
    )
    cognitive_activity_babies_ids = fields.Many2many(
        'icp.cognitive.activity', 'icp_cognitive_baby_act',
        string='Cognitive activities (0-5)', readonly=True
    )
    cognitive_activity_kids_ids = fields.Many2many(
        'icp.cognitive.activity', 'icp_cognitive_kid_act',
        string='Cognitive activities (6-11)', readonly=True
    )
    cognitive_activity_ados_ids = fields.Many2many(
        'icp.cognitive.activity', 'icp_cognitive_ado_act',
        string='Cognitive activities (12+)', readonly=True
    )
    physical_activity_babies_ids = fields.Many2many(
        'icp.physical.activity', 'icp_physical_baby_act',
        string='Physical activities (0-5)', readonly=True
    )
    physical_activity_kids_ids = fields.Many2many(
        'icp.physical.activity', 'icp_physical_kid_act',
        string='Physical activities (6-11)', readonly=True
    )
    physical_activity_ados_ids = fields.Many2many(
        'icp.physical.activity', 'icp_physical_ado_act',
        string='Physical activities (12+)', readonly=True
    )
    socio_activity_babies_ids = fields.Many2many(
        'icp.sociological.activity', 'icp_socio_baby_act',
        string='Sociological activities (0-5)', readonly=True
    )
    socio_activity_kids_ids = fields.Many2many(
        'icp.sociological.activity', 'icp_socio_kid_act',
        string='Sociological activities (6-11)', readonly=True
    )
    socio_activity_ados_ids = fields.Many2many(
        'icp.sociological.activity', 'icp_socio_ado_act',
        string='Sociological activities (12+)', readonly=True
    )
    reservation_id = fields.Many2one(
        'icp.reservation', string='Project Reservation', ondelete='cascade'
    )
    activities_for_parents = fields.Char(readonly=True)

    # Community information
    #######################
    community_name = fields.Char(readonly=True)
    community_population = fields.Integer(readonly=True)
    primary_ethnic_group_name = fields.Char(readonly=True)
    primary_language_id = fields.Many2one(
            'res.lang.compassion', 'Primary language', readonly=True)
    primary_adults_occupation_ids = fields.Many2many(
        'icp.community.occupation', string='Primary adults occupation',
        readonly=True
    )
    monthly_income = fields.Float(
        help='Average family income in local currency', readonly=True)
    unemployment_rate = fields.Float(readonly=True)
    annual_primary_school_cost = fields.Float(
        readonly=True, help='In local currency')
    annual_secondary_school_cost = fields.Float(
        readonly=True, help='In local currency')
    school_cost_paid_ids = fields.Many2many(
        'icp.school.cost', string='School costs paid by ICP', readonly=True
    )
    school_year_begins = fields.Selection('_get_months', readonly=True)
    closest_city = fields.Char(readonly=True)
    closest_airport_distance = fields.Float(
        help='Distance in kilometers', readonly=True)
    time_to_airport = fields.Float(help='Time in minutes', readonly=True)
    transport_mode_to_airport = fields.Char(readonly=True)
    time_to_medical_facility = fields.Char(readonly=True)
    community_locale = fields.Selection([
        ('City', 'City'),
        ('Rural', 'Rural'),
        ('Town', 'Town'),
        ('Village', 'Village'),
    ], readonly=True)
    community_climate = fields.Selection([
        ('Dry', 'Dry'),
        ('Humid', 'Humid'),
        ('Moderate', 'Moderate'),
    ], readonly=True)
    community_terrain = fields.Selection([
        ('Coastal', _('coastal')),
        ('Desert', _('desert')),
        ('Forested', _('forested')),
        ('Hilly', _('hilly')),
        ('Island', _('island')),
        ('Jungle', _('jungle')),
        ('Lake', _('lake')),
        ('Mountainous', _('mountainous')),
        ('Other', 'Other'),
        ('Plains/Flat Land', _('plains')),
        ('Valley', _('valley')),
    ], readonly=True)
    typical_roof_material = fields.Selection('_get_materials', readonly=True)
    typical_floor_material = fields.Selection('_get_materials', readonly=True)
    typical_wall_material = fields.Selection('_get_materials', readonly=True)
    average_coolest_temperature = fields.Float(readonly=True)
    coolest_month = fields.Selection('_get_months', readonly=True)
    average_warmest_temperature = fields.Float(readonly=True)
    warmest_month = fields.Selection('_get_months', readonly=True)
    rainy_month_ids = fields.Many2many(
        'connect.month', string='Rainy months', readonly=True
    )
    planting_month_ids = fields.Many2many(
        'connect.month', string='Planting months', readonly=True
    )
    harvest_month_ids = fields.Many2many(
        'connect.month', string='Harvest months', readonly=True
    )
    hunger_month_ids = fields.Many2many(
        'connect.month', string='Hunger months', readonly=True
    )
    cultural_rituals = fields.Char(readonly=True)
    economic_needs = fields.Char(readonly=True)
    health_needs = fields.Char(readonly=True)
    education_needs = fields.Char(readonly=True)
    social_needs = fields.Text(readonly=True)
    spiritual_needs = fields.Text(readonly=True)
    primary_diet_ids = fields.Many2many(
        'icp.diet', string='Primary diet', readonly=True)

    # Partnership
    #############
    partnership_start_date = fields.Date(oldname='start_date', readonly=True)
    program_start_date = fields.Date(readonly=True)
    program_end_date = fields.Date(readonly=True)

    # Program Settings
    ##################
    first_scheduled_letter = fields.Selection('_get_months', readonly=True)
    second_scheduled_letter = fields.Selection('_get_months', readonly=True)

    # Project needs
    ###############
    project_need_ids = fields.One2many(
        'compassion.project.need', 'project_id', 'Project needs', readonly=True
    )

    # Project state
    ###############
    lifecycle_ids = fields.One2many(
        'compassion.project.ile', 'project_id', 'Lifecycle events',
        readonly=True
    )
    suspension = fields.Selection([
        ('suspended', _('Suspended')),
        ('fund-suspended', _('Suspended & fund retained'))], 'Suspension',
        compute='_set_suspension_state', store=True,
        track_visibility='onchange')
    status = fields.Selection(
        '_get_state', track_visibility='onchange', default='A', readonly=True)
    status_date = fields.Date(
        'Last status change', track_visibility='onchange', readonly=True)
    status_comment = fields.Text(
        related='lifecycle_ids.details', store=True)
    hold_cdsp_funds = fields.Boolean(related='lifecycle_ids.hold_cdsp_funds')
    hold_csp_funds = fields.Boolean(related='lifecycle_ids.hold_csp_funds')
    hold_gifts = fields.Boolean(related='lifecycle_ids.hold_gifts')
    hold_s2b_letters = fields.Boolean(related='lifecycle_ids.hold_s2b_letters')
    hold_b2s_letters = fields.Boolean(related='lifecycle_ids.hold_b2s_letters')

    # Project Descriptions
    ######################
    description_en = fields.Text('English description', readonly=True)
    description_fr = fields.Text('French description', readonly=True)
    description_de = fields.Text('German description', readonly=True)
    description_it = fields.Text('Italian description', readonly=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('icp_id')
    def _compute_field_office(self):
        fo_obj = self.env['compassion.field.office']
        for project in self:
            fo = fo_obj.search([('field_office_id', '=', project.icp_id[:2])])
            project.field_office_id = fo.id

    @api.model
    def _get_months(self):
        return self.env['connect.month'].get_months_selection()

    @api.depends('lifecycle_ids')
    @api.one
    def _set_suspension_state(self):
        old_value = self.read(['suspension'])[0]['suspension']
        if self.lifecycle_ids:
            last_info = self.lifecycle_ids[0]
            if last_info.type == 'Suspension':
                suspension_status = 'fund-suspended' if \
                    last_info.hold_cdsp_funds else 'suspended'
                if suspension_status != old_value:
                    self.suspend_funds()
                self.suspension = suspension_status
            elif last_info.type == 'Reactivation':
                if old_value == 'fund-suspended':
                    self._reactivate_project()
                self.suspension = False

    @api.model
    def _get_state(self):
        return [
            ('A', _('Active')),
            ('P', _('Phase-out')),
            ('T', _('Terminated')),
            ('TR', _('Transitioned')),
            ('S', _('Suspended')),
        ]

    def _get_materials(self):
        return [
            ('Bamboo', _('bamboo')),
            ('Brick/Block/Cement', _('brick, block and cement')),
            ('Cardboard', _('cardboard')),
            ('Cement', _('cement')),
            ('Cloth/Carpet', _('cloth and carpet')),
            ('Dirt', _('dirt')),
            ('Leaves/Grass/Thatch', _('leaves, grass and thatch')),
            ('Leaves/Grass', _('leaves and grass')),
            ('Mud/Earth/Clay/Adobe', _('mud, earth, clay and adobe')),
            ('Other', 'Other'),
            ('Plastic Sheets', _('plastic sheets')),
            ('Tile', _('tile')),
            ('Tin/Corrugated Iron', _('tin')),
            ('Wood', _('wood')),
        ]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        project = super(CompassionProject, self).create(vals)
        project.update_informations(async_mode=True)
        return project

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.one
    def suspend_funds(self):
        """ Hook to perform some action when project is suspended.
        By default: log a message.
        """
        self.message_post(
            "The project was suspended and funds are retained.",
            "Project Suspended", 'comment')
        return True

    @api.model
    def set_missing_field_offices(self):
        self.search([('field_office_id', '=', False)])._compute_field_office()
        return True

    @api.multi
    def get_activities(self, max_per_type=sys.maxint):
        icp_activities = list()
        all_activities = [
            (self.mapped('spiritual_activity_babies_ids') +
             self.mapped('spiritual_activity_kids_ids') +
             self.mapped('spiritual_activity_ados_ids')).sorted(),
            (self.mapped('cognitive_activity_babies_ids') +
             self.mapped('cognitive_activity_kids_ids') +
             self.mapped('cognitive_activity_ados_ids')).sorted(),
            (self.mapped('physical_activity_babies_ids') +
             self.mapped('physical_activity_kids_ids') +
             self.mapped('physical_activity_ados_ids')).sorted(),
            (self.mapped('socio_activity_babies_ids') +
             self.mapped('socio_activity_kids_ids') +
             self.mapped('socio_activity_ados_ids')).sorted()
        ]
        for activities in all_activities:
            max_number_act = min(len(activities), max_per_type)
            icp_activities.extend(activities[:max_number_act].mapped('value'))
        return icp_activities

    def details_answer(self, vals):
        """ Called when receiving the answer of GetDetails message. """
        self.ensure_one()
        self.write(vals)
        self.generate_descriptions()
        return True

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def update_informations(self, context=None, async_mode=False):
        """ Get the most recent informations for selected projects and update
            them accordingly. """
        message_obj = self.env['gmc.message.pool']
        action_id = self.env.ref('child_compassion.icp_details').id
        message_vals = {
            'action_id': action_id,
            'object_id': self.id,
        }
        message_obj.with_context(async_mode=async_mode).create(message_vals)
        return True

    @api.multi
    def generate_descriptions(self):
        for project in self:
            project.description_fr = ProjectDescriptionFr.gen_fr_translation(
                project.with_context(lang='fr_CH'))
            project.description_de = ProjectDescriptionDe.gen_de_translation(
                project.with_context(lang='de_DE'))
            project.description_it = ProjectDescriptionIt.gen_it_translation(
                project.with_context(lang='it_IT'))

        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.one
    def _reactivate_project(self):
        """ To perform some actions when project is reactivated """
        self.message_post(
            "The project is reactivated.",
            "Project Reactivation", 'comment')
        return True
