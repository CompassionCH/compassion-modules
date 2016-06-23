# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Kevin Cristi, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
from openerp import models, fields, api, _

from ..wizards.project_description_fr import Project_description_fr

logger = logging.getLogger(__name__)


class CompassionProject(models.Model):
    """ A compassion project """
    _name = 'compassion.project'
    _rec_name = 'icp_id'
    _inherit = 'mail.thread'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # General Information
    #####################
    icp_id = fields.Char(required=True, oldname='code')
    name = fields.Char()
    child_center_original_name = fields.Char()
    local_church_name = fields.Char()
    local_church_original_name = fields.Char()
    website = fields.Char()
    social_media_site = fields.Char()
    involvement_ids = fields.Many2many('icp.involvement', string='Involvement')
    available_for_visits = fields.Boolean()
    nb_csp_kids = fields.Integer('CSP kids count')
    nb_cdsp_kids = fields.Integer('CDSP kids count')
    last_update_date = fields.Date('Last update')
    engaged_partner_ids = fields.Many2many(
        'compassion.global.partner', string='GP with church engagement'
    )

    # Location information
    ######################
    country = fields.Char()
    country_id = fields.Many2one('res.country', 'Country',
                                 related='field_office_id.country_id')
    street = fields.Char()
    city = fields.Char()
    state_province = fields.Char()
    zip_code = fields.Char()
    gps_latitude = fields.Float()
    gps_longitude = fields.Float()
    cluster = fields.Char()
    territory = fields.Char()
    field_office_id = fields.Many2one(
        'compassion.field.office', compute='_compute_field_office', store=True)

    # Church information
    ####################
    church_foundation_date = fields.Date()
    church_denomination = fields.Char()
    international_affiliation = fields.Char()
    ministry_ids = fields.Many2many(
        'icp.church.ministry', string='Church ministries'
    )
    preferred_lang_id = fields.Many2one(
        'res.lang.compassion', 'Church preferred language')
    number_church_members = fields.Integer()
    weekly_child_attendance = fields.Integer()
    implemented_program_ids = fields.Many2many(
        'icp.program', string='Programs implemented'
    )
    interested_program_ids = fields.Many2many(
        'icp.program', string='Programs of interest'
    )

    # Church infrastructure information
    ###################################
    church_building_size = fields.Float(help='Unit is square meters')
    church_ownership = fields.Selection([
        ('Rented', 'Rented'),
        ('Owned', 'Owned'),
    ])
    facility_ids = fields.Many2many(
        'icp.church.facility', string='Church facilities'
    )
    nb_staff_computers = fields.Char(size=2)
    nb_child_computers = fields.Char(size=2)
    nb_classrooms = fields.Char(size=2)
    nb_latrines = fields.Char(size=2)
    church_internet_access = fields.Selection([
        ('No', 'No'),
        ('Yes, onsite through one or more computers ', 'Onsite'),
        ('Yes, but offsite', 'Offsite'),

    ])
    mobile_device_ids = fields.Many2many(
        'icp.mobile.device', string='Mobile devices'
    )
    utility_ids = fields.Many2many(
        'icp.church.utility', string='Church utilities'
    )
    electrical_power = fields.Selection([
        ('Not Available', 'Not Available'),
        ('Available Sometimes', 'Available Sometimes'),
        ('Available Most of the Time', 'Available Most of the Time'),
    ])

    # ICP Activities
    ################
    spiritual_activity_babies_ids = fields.Many2many(
        'icp.spiritual.activity', string='Spiritual activities (0-5)'
    )
    spiritual_activity_kids_ids = fields.Many2many(
        'icp.spiritual.activity', string='Spiritual activities (6-11)'
    )
    spiritual_activity_ados_ids = fields.Many2many(
        'icp.spiritual.activity', string='Spiritual activities (12+)'
    )
    cognitive_activity_babies_ids = fields.Many2many(
        'icp.cognitive.activity', string='Cognitive activities (0-5)'
    )
    cognitive_activity_kids_ids = fields.Many2many(
        'icp.cognitive.activity', string='Cognitive activities (6-11)'
    )
    cognitive_activity_ados_ids = fields.Many2many(
        'icp.cognitive.activity', string='Cognitive activities (12+)'
    )
    physical_activity_babies_ids = fields.Many2many(
        'icp.physical.activity', string='Physical activities (0-5)'
    )
    physical_activity_kids_ids = fields.Many2many(
        'icp.physical.activity', string='Physical activities (6-11)'
    )
    physical_activity_ados_ids = fields.Many2many(
        'icp.physical.activity', string='Physical activities (12+)'
    )
    socio_activity_babies_ids = fields.Many2many(
        'icp.sociological.activity', string='Sociological activities (0-5)'
    )
    socio_activity_kids_ids = fields.Many2many(
        'icp.sociological.activity', string='Sociological activities (6-11)'
    )
    socio_activity_ados_ids = fields.Many2many(
        'icp.sociological.activity', string='Sociological activities (12+)'
    )
    activities_for_parents = fields.Char()

    # Community information
    #######################
    community_name = fields.Char()
    community_population = fields.Integer()
    primary_ethnic_group_name = fields.Char()
    primary_language_id = fields.Many2one(
            'res.lang.compassion', 'Primary language')
    primary_adults_occupation_ids = fields.Many2many(
        'icp.community.occupation', string='Primary adults occupation'
    )
    monthly_income = fields.Float(help='Average family income in local '
                                       'currency')
    unemployment_rate = fields.Float()
    annual_primary_school_cost = fields.Float()
    annual_secondary_school_cost = fields.Float()
    school_cost_paid_ids = fields.Many2many(
        'icp.school.cost', string='School costs paid by ICP'
    )
    school_year_begins = fields.Selection('_get_months')
    closest_city = fields.Char()
    closest_airport_distance = fields.Float(help='Distance in kilometers')
    time_to_airport = fields.Float(help='Time in minutes')
    transport_mode_to_airport = fields.Char()
    time_to_medical_facility = fields.Char()
    community_locale = fields.Selection([
        ('City', 'City'),
        ('Rural', 'Rural'),
        ('Town', 'Town'),
        ('Village', 'Village'),
    ])
    community_climate = fields.Selection([
        ('Dry', 'Dry'),
        ('Humid', 'Humid'),
        ('Moderate', 'Moderate'),
    ])
    community_terrain = fields.Selection([
        ('Coastal', 'Coastal'),
        ('Desert', 'Desert'),
        ('Forested', 'Forested'),
        ('Hilly', 'Hilly'),
        ('Island', 'Island'),
        ('Jungle', 'Jungle'),
        ('Lake', 'Lake'),
        ('Mountainous', 'Mountainous'),
        ('Other', 'Other'),
        ('Plains/Flat Land', 'Plains/Flat Land'),
        ('Valley', 'Valley'),
    ])
    typical_roof_material = fields.Selection([
        ('Bamboo', 'Bamboo'),
        ('Cardboard', 'Cardboard'),
        ('Cement', 'Cement'),
        ('Leaves/Grass/Thatch', 'Leaves/Grass/Thatch'),
        ('Other', 'Other'),
        ('Plastic Sheets', 'Plastic Sheets'),
        ('Tile', 'Tile'),
        ('Tin/Corrugated Iron', 'Tin/Corrugated Iron'),
        ('Wood', 'Wood'),
    ])
    typical_floor_material = fields.Selection([
        ('Bamboo', 'Bamboo'),
        ('Cardboard', 'Cardboard'),
        ('Cement', 'Cement'),
        ('Cloth/Carpet', 'Cloth/Carpet'),
        ('Dirt', 'Dirt'),
        ('Leave/Grass', 'Leave/Grass'),
        ('Other', 'Other'),
        ('Tile', 'Tile'),
        ('Wood', 'Wood'),
    ])
    typical_wall_material = fields.Selection([
        ('Bamboo', 'Bamboo'),
        ('Brick/Block/Cement', 'Brick/Block/Cement'),
        ('Cardboard', 'Cardboard'),
        ('Leaves/Grass', 'Leaves/Grass'),
        ('Mud/Earth/Clay/Adobe', 'Mud/Earth/Clay/Adobe'),
        ('Other', 'Other'),
        ('Plastic', 'Plastic'),
        ('Tin', 'Tin'),
        ('Wood', 'Wood'),
    ])
    average_coolest_temperature = fields.Float()
    coolest_month = fields.Selection('_get_months')
    average_warmest_temperature = fields.Float()
    warmest_month = fields.Selection('_get_months')
    rainy_month_ids = fields.Many2many(
        'connect.month', string='Rainy months'
    )
    planting_month_ids = fields.Many2many(
        'connect.month', string='Planting months'
    )
    harvest_month_ids = fields.Many2many(
        'connect.month', string='Harvest months'
    )
    hunger_month_ids = fields.Many2many(
        'connect.month', string='Hunger months'
    )
    cultural_rituals = fields.Char()
    economic_needs = fields.Char()
    health_needs = fields.Char()
    education_needs = fields.Char()
    social_needs = fields.Text()
    spiritual_needs = fields.Text()
    primary_diet_ids = fields.Many2many('icp.diet', string='Primary diet')

    # Partnership
    #############
    partnership_start_date = fields.Date(oldname='start_date')
    program_start_date = fields.Date()

    # Program Settings
    ##################
    first_scheduled_letter = fields.Selection('_get_months')
    second_scheduled_letter = fields.Selection('_get_months')

    # Project needs
    ###############
    project_need_ids = fields.One2many(
        'compassion.project.need', 'project_id', 'Project needs'
    )

    # Project state
    ###############
    lifecycle_ids = fields.One2many(
        'compassion.project.ile', 'project_id', 'Lifecycle events'
    )
    suspension = fields.Selection([
        ('suspended', _('Suspended')),
        ('fund-suspended', _('Suspended & fund retained'))], 'Suspension',
        compute='_set_suspension_state', store=True,
        track_visibility='onchange')
    status = fields.Selection(
        '_get_state', track_visibility='onchange', default='A')
    status_date = fields.Date(
        'Last status change', track_visibility='onchange')
    status_comment = fields.Char()
    hold_cdsp_funds = fields.Boolean(related='lifecycle_ids.hold_cdsp_funds')
    hold_csp_funds = fields.Boolean(related='lifecycle_ids.hold_csp_funds')
    hold_gifts = fields.Boolean(related='lifecycle_ids.hold_gifts')
    hold_s2b_letters = fields.Boolean(related='lifecycle_ids.hold_s2b_letters')
    hold_b2s_letters = fields.Boolean(related='lifecycle_ids.hold_b2s_letters')

    # Project Descriptions
    ######################
    description_en = fields.Text('English description')
    description_fr = fields.Text('French description')
    description_de = fields.Text('German description')
    description_it = fields.Text('Italian description')

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
            ('T', _('Terminated'))
        ]

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

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def update_informations(self):
        """ Get the most recent informations for selected projects and update
            them accordingly. """
        # TODO Redefine this
        self.generate_descriptions()
        return True

    @api.multi
    def generate_descriptions(self):
        # TODO Implement with new modelisation
        for project in self:
            project.description_fr = Project_description_fr.gen_fr_translation(
                project.with_context(lang='fr_CH'))

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
