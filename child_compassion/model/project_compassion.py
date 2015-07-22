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

import requests
import urllib3
import certifi
import json
import logging

from openerp import models, fields, api, exceptions, _
from openerp.tools.config import config

logger = logging.getLogger(__name__)


class compassion_project(models.Model):
    """ A compassion project """
    _name = 'compassion.project'
    _rec_name = 'code'
    _inherit = 'mail.thread'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # General Information
    #####################
    name = fields.Char(size=128, required=True, default='/')
    code = fields.Char(size=128, required=True)
    country_id = fields.Many2one('compassion.country', 'Country')
    type = fields.Selection([
        ('CDSP', 'CDSP'), ('CSP', 'CSP')], 'Program type')
    start_date = fields.Date('Partnership begining')
    stop_date = fields.Date('Partnership ending')
    last_update_date = fields.Date('Last update')
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
    disburse_funds = fields.Boolean(track_visibility='onchange')
    disburse_gifts = fields.Boolean(track_visibility='onchange')
    disburse_unsponsored_funds = fields.Boolean(track_visibility='onchange')
    new_sponsorships_allowed = fields.Boolean(track_visibility='onchange')
    additional_quota_allowed = fields.Boolean(track_visibility='onchange')

    # Project Descriptions
    ######################
    description_en = fields.Text('English description')
    description_fr = fields.Text('French description')
    description_de = fields.Text('German description')
    description_it = fields.Text('Italian description')

    has_desc_fr = fields.Boolean('FR', compute='_has_desc')
    has_desc_de = fields.Boolean('DE', compute='_has_desc')
    has_desc_it = fields.Boolean('IT', compute='_has_desc')
    has_desc_en = fields.Boolean('EN', compute='_has_desc')

    needs_fr = fields.Text('French needs')
    needs_de = fields.Text('German needs')
    needs_it = fields.Text('Italian needs')

    # Community Information
    #######################
    local_church_name = fields.Char('Local church name')
    hiv_category = fields.Selection([
        ('AFFCTD', _('Affected')),
        ('NOTAFF', _('Not affected'))],
        _('HIV/Aids category for project area'),
        track_visibility='onchange')
    month_school_year_begins = fields.Selection([
        ('1', _('January')), ('2', _('February')), ('3', _('March')),
        ('4', _('April')), ('5', _('May')), ('6', _('June')),
        ('7', _('July')), ('8', _('August')), ('9', _('September')),
        ('10', _('October')), ('11', _('November')), ('12', _('December'))
    ], 'Month school begins each year')
    country_denomination = fields.Char('Local denomination')
    western_denomination = fields.Char('Western denomination')
    community_name = fields.Char('Community name')
    country_common_name = fields.Text('Country common name')

    # Miscellaneous Information (retrieved from community API)
    ##########################################################
    #   a. Automatic translated values
    floor_material_ids = fields.Many2many(
        'compassion.translated.value', 'project_property_to_value',
        'project_id', 'value_id', _('Floor material'),
        domain=[('property_name', '=', 'floor_material')],
        track_visibility='onchange')
    wall_material_ids = fields.Many2many(
        'compassion.translated.value', 'project_property_to_value',
        'project_id', 'value_id', _('Wall material'),
        domain=[('property_name', '=', 'wall_material')],
        track_visibility='onchange')
    roof_material_ids = fields.Many2many(
        'compassion.translated.value', 'project_property_to_value',
        'project_id', 'value_id', _('Roof material'),
        domain=[('property_name', '=', 'roof_material')],
        track_visibility='onchange')
    spoken_languages_ids = fields.Many2many(
        'compassion.translated.value', 'project_property_to_value',
        'project_id', 'value_id', _('Spoken languages'),
        domain=[('property_name', '=', 'spoken_languages')],
        track_visibility='onchange')
    primary_diet_ids = fields.Many2many(
        'compassion.translated.value', 'project_property_to_value',
        'project_id', 'value_id', _('Primary diet'),
        domain=[('property_name', '=', 'primary_diet')],
        track_visibility='onchange')
    health_problems_ids = fields.Many2many(
        'compassion.translated.value', 'project_property_to_value',
        'project_id', 'value_id', _('Health problems'),
        domain=[('property_name', '=', 'health_problems')],
        track_visibility='onchange')
    primary_occupation_ids = fields.Many2many(
        'compassion.translated.value', 'project_property_to_value',
        'project_id', 'value_id', _('Primary occupation'),
        domain=[('property_name', '=', 'primary_occupation')],
        track_visibility='onchange')
    terrain_description_ids = fields.Many2many(
        'compassion.translated.value', 'project_property_to_value',
        'project_id', 'value_id', _('Terrain description'),
        domain=[('property_name', '=', 'terrain_description')],
        track_visibility='onchange')
    distance_from_closest_city_ids = fields.Many2many(
        'compassion.translated.value', 'project_property_to_value',
        'project_id', 'value_id', _('Distance from closest city'),
        domain=[('property_name', '=', 'distance_from_closest_city')],
        track_visibility='onchange')
    #   b. Static Values
    gps_latitude = fields.Float(_('GPS latitude'))
    gps_longitude = fields.Float(_('GPS longitude'))
    unemployment_rate = fields.Float(
        _('Unemployment rate'), track_visibility='onchange')
    closest_city = fields.Char(_('Closest city'))
    community_population = fields.Integer(
        _('Community population'), track_visibility='onchange')
    monthly_income = fields.Float(
        _('Monthly income'), track_visibility='onchange')
    #   c. Non translated text
    economic_needs = fields.Text(_('Economic needs'))
    education_needs = fields.Text(_('Education needs'))
    social_needs = fields.Text(_('Social needs'))
    spiritual_needs = fields.Text(_('Spiritual needs'))

    #   d. Age groups section
    age_group_ids = fields.One2many(
        'compassion.project.age.group', 'project_id',
        _('Age group'),
        readonly=True, track_visibility="onchange")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends(
        'disburse_funds', 'disburse_gifts', 'disburse_unsponsored_funds',
        'new_sponsorships_allowed', 'additional_quota_allowed')
    @api.one
    def _set_suspension_state(self):
        if self.id:
            if self.status in ('A', 'P') and not (
                    self.disburse_gifts and self.disburse_funds and
                    self.disburse_unsponsored_funds and
                    self.new_sponsorships_allowed and
                    self.additional_quota_allowed):
                status = 'suspended' if self.disburse_funds \
                    else 'fund-suspended'

                if status == 'fund-suspended' and \
                        self.suspension != 'fund-suspended':
                    self.suspend_funds()
                self.suspension = status
            elif self.suspension == 'fund-suspended':
                self.suspension = False
                self._reactivate_project()

    def _has_desc(self):
        for project in self:
            vals = {
                'has_desc_fr': bool(project.description_fr),
                'has_desc_de': bool(project.description_de),
                'has_desc_it': bool(project.description_it),
                'has_desc_en': bool(project.description_en)
            }
            project.write(vals)

    @api.model
    def _get_state(self):
        return [
            ('A', _('Active')),
            ('P', _('Phase-out')),
            ('T', _('Terminated'))
        ]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """Get informations of project on creation. """
        res = super(compassion_project, self).create(vals)
        res.update_informations()
        return res

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
    def https_get(self, url):
        """" Try to fetch URL with secure connection. """
        http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',  # Force certificate check.
            ca_certs=certifi.where(),   # Path to the Certifi bundle.
        )
        r = None
        try:
            r = http.request('GET', url).data
        except urllib3.exceptions.SSLError:
            logger.error("Could not connect with SSL CERT.")
            r = requests.get(url).text
        return r

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def update_informations(self):
        """ Get the most recent informations for selected projects and update
            them accordingly. """
        for project in self:
            values = None
            try:
                values, community_id = self._update_program_info(project.code)
                values.update(self._update_community_info(community_id))
                if values['type'] == 'CDSP':
                    values.update(self._update_cdsp_info(project.code))
                project._get_age_groups()
            except exceptions.Warning as e:
                # Log error
                project.message_post(e[1], e[0], 'comment')
            finally:
                if values:
                    project.write(values)

        return True

    @api.multi
    def generate_descriptions(self):
        for project in self:
            if not project.last_update_date:
                raise exceptions.Warning(
                    _('Generation error'),
                    _('Missing information for project %s. Please update its '
                      'information before generating the descriptions') %
                    project.code)

        return {
            'name': _('Description generation'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'auto_description_form',
            'res_model': 'project.description.wizard',
            'target': 'new',
        }

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

    @api.model
    def _update_program_info(self, project_code):
        """ Calls the "ProgramImplementors" REST API.
            Returns the information in a dictionary of the form
            {'field_name': 'value'}, and the community_id used
            to call the GetCommunity API.
            See http://developer.compassion.com/docs/read/
                private_cornerstone_test/REST_Get_Program_Implementor
            for more information.
        """
        prog_impl = self._cornerstone_fetch(project_code,
                                            'programimplementors')
        values = {
            'type': prog_impl.get('programImplementorTypeCode'),
            'local_church_name': prog_impl.get('organizationName'),
            'hiv_category': prog_impl.get('hIVCategory'),
            'month_school_year_begins': prog_impl.get(
                'monthSchoolYearBegins'),
            'country_denomination': prog_impl.get('countryDenomination'),
            'western_denomination': prog_impl.get('westernDenomination'),
            'community_name': prog_impl.get('communityName'),
            'country_id': self._update_country(
                prog_impl.get('isoCountryCode')),
            'country_common_name': prog_impl.get('countryCommonName'),
        }
        community_id = prog_impl.get('communityID')
        return {field_name: value for field_name, value in values.iteritems()
                if value}, community_id

    @api.model
    def _update_country(self, country_code):
        """ Finds the country having the given country_code or
            creates one.
            Returns the country_id of the country object.
        """
        country_obj = self.env['compassion.country']
        countries = country_obj.search([('iso_code', '=', country_code)])
        if countries:
            country = countries[0]
        else:
            country = country_obj.create({'iso_code': country_code})
            country.update_informations()
        return country.id

    def _get_age_groups(self):
        """ Get age group from compassion webservice and l
            Returns ids of generated age_groups or None if failed """
        self.ensure_one()
        # Delete old age_groups
        self.age_group_ids.unlink()
        json_data = self._cornerstone_fetch(self.code + '/agegroups',
                                            'cdspimplementors')
        value_obj = self.env['compassion.translated.value']
        age_project_obj = self.env['compassion.project.age.group']
        for group in json_data['projectAgeGroupCollection']:
            values = list()
            vals = {
                'project_id': self.id,
                'low_age': group['lowAge'],
                'high_age': group['highAge'],
                'school_hours': group['schoolHours'],
            }
            values.extend(value_obj.get_value_ids(
                group['schoolDays'].split(','),
                'school_days'))
            values.extend(value_obj.get_value_ids(
                group['schoolMonths'].split(','),
                'school_months'))

            vals['school_days_ids'] = [(6, 0, [v for v in values if v])]
            age_project_obj.create(vals)
        return True

    @api.model
    def _update_community_info(self, community_id):
        """ Call the "REST Get Community" API from Compassion.
        See http://developer.compassion.com/docs/read/
            private_cornerstone_test/REST_Get_Community for more information.
        Returns: the information in a dictionary of the form
                 {'field_name': 'value'}
        """
        # Standard fields retrieval
        json_values = self._cornerstone_fetch(community_id, 'communities')
        values = {
            'unemployment_rate': json_values['unemploymentRate'],
            'community_population': json_values['communityPopulation'],
            'monthly_income': json_values['familyMonthlyIncome'],
            'economic_needs': json_values['economicNeeds'],
            'education_needs': json_values['educationalNeeds'],
            'social_needs': json_values['socialNeeds'],
            'spiritual_needs': json_values['spiritualNeeds'],
            'closest_city': json_values['closestCityName'],
        }

        # Automatic translated fields retrieval
        # Dictionary key -> JSON field name;
        # Dictionary value -> (Odoo field name, separator between values)
        json_misc_tags = {
            'terrainDescription': ('terrain_description', '/'),
            'typicalFloorBuildingMaterialDescription': ('floor_material', '/'),
            'typicalWallBuildingMaterialDescription': ('wall_material', '/'),
            'typicalRoofBuildingMaterialDescription': ('roof_material', '/'),
            'primaryEthnicGroup': ('spoken_languages', '?'),
            'primaryDiet': ('primary_diet', ','),
            'commonHealthProblems': ('health_problems', ', '),
            'primaryOccupationTitle': ('primary_occupation', '/'),
            'distanceFromClosestCity': ('distance_from_closest_city', '?'),
        }

        # Get the property values ids
        # (ids of 'compassion.translated.value' objects)
        multi_value = []
        value_obj = self.env['compassion.translated.value']
        for json_key, field_tuple in json_misc_tags.iteritems():
            field_name = field_tuple[0]
            separator = field_tuple[1]

            multi_value.extend(value_obj.get_value_ids(
                json_values[json_key].split(separator),
                field_name))

        """ Only one field need to get all the many2many relations.
        Then all other fields will get their correct values
        because of the domain set on the property_name.
        This is because there is only one physical underlying
        many2many relation.
        [(6, 0, [ids])] is a standard way to set a many2many field in Odoo.
        """
        values['primary_diet_ids'] = [(6, 0, [v for v in multi_value if v])]

        return {field_name: value for field_name, value in values.iteritems()
                if value}

    @api.model
    def _update_cdsp_info(self, project_code):
        """ Call the "REST Get CDSP" API from Compassion.
        See http://developer.compassion.com/docs/read/
            private_cornerstone_test/Get_CDSP_Implementor
            for more information.
        Returns: the information in a dictionary of the form
                 {'field_name': 'value'}
        """
        json_values = self._cornerstone_fetch(project_code, 'cdspimplementors')
        values = {
            'name': json_values.get('name'),
            'start_date': json_values.get('startDate') or False,
            'stop_date': json_values.get('stopDate') or False,
            'last_update_date': json_values.get('lastUpdateDate') or False,
            'status': json_values.get('status'),
            'status_date': json_values.get('statusDate') or False,
            'status_comment': json_values.get('statusComment'),
            'description_en': json_values.get('description'),
            'gps_latitude': json_values.get(
                'gPSCoordinateLatitudeHighPrecision'),
            'gps_longitude': json_values.get(
                'gPSCoordinateLongitudeHighPrecision'),
            'disburse_funds': json_values.get('disburseFunds'),
            'disburse_gifts': json_values.get('disburseGifts'),
            'disburse_unsponsored_funds': json_values.get(
                'disburseUnsponsoredFunds'),
            'new_sponsorships_allowed': json_values.get(
                'newSponsorshipsAllowed'),
            'additional_quota_allowed': json_values.get(
                'additionalQuotaAllowed'),
        }
        return {field_name: value for field_name, value in values.iteritems()}

    @api.model
    def _cornerstone_fetch(self, project_code, api_mess):
        """ Construct the correct URL to call Compassion Cornerstone APIs.
        Returns the JSON object of the response."""
        url = config.get('compass_url')
        api_key = config.get('compass_api_key')
        if not url or not api_key:
            raise exceptions.Warning(
                'ConfigError',
                _('Missing compass_url or compass_api_key in conf file'))
        if url.endswith('/'):
            url = url[:-1]

        url += ('/ci/v1/' + api_mess + '/' + project_code + '?api_key=' +
                api_key)

        # Send the request and retrieve the result.
        r = self.https_get(url)
        json_result = None
        try:
            json_result = json.loads(r)
        except:
            raise exceptions.Warning(
                'Error calling webservice',
                'Error calling %s for project %s' % (api_mess, project_code))
        return json_result
