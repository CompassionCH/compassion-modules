# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import requests
import json
import logging
logger = logging.getLogger(__name__)

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools.config import config

class compassion_project(orm.Model):
    """ A compassion project """
    _name = 'compassion.project'
    _columns = {
        'name': fields.char(_("Name"),size=128,required=True),
        'code': fields.char(_("Project code"),size=128,required=True),
        'type': fields.selection([
            ('CDSP', 'CDSP'),
            ('CSP', 'CSP')], _('Program type')),
        'start_date': fields.date(_('Partnership begining')),
        'stop_date': fields.date(_('Partnership ending')),
        'last_update_date': fields.date(_('Last update')),
        'suspension': fields.selection([
            ('suspended', _('Suspended')),
            ('fund-suspended', _('Suspended & fund retained'))],
            _('Suspension')),
        'status': fields.selection([
            ('A', _('Active')),
            ('P', _('Phase-out')),
            ('T', _('Terminated'))], _('Status')),
        'status_date': fields.date(_('Last status change')),
        'status_comment': fields.char(_('Status comment')),
        'description_en': fields.text(_('English description')),
        'description_fr': fields.text(_('French description')),
        'description_de': fields.text(_('German description')),
        'description_it': fields.text(_('Italian description')),
        'gps_latitude': fields.float(_('GPS latitude')),
        'gps_longitude': fields.float(_('GPS longitude')),
        'local_church_name': fields.char(_('Local church name')),
        'hiv_category': fields.selection([
            ('AFFCTD', _('Affected')),
            ('NOTAFF', _('Not affected'))],
            _('HIV/Aids category for project area')),
        'month_school_year_begins': fields.selection([
            ('1', _('January')), ('2', _('February')), ('3', _('March')),
            ('4', _('April')), ('5', _('May')), ('6', _('June')),
            ('7', _('July')), ('8', _('August')), ('9', _('September')),
            ('10', _('October')), ('11', _('November')), ('12', _('December'))
            ], _('Month school begins each year')),
        'country_denomination': fields.char(_('Local denomination')),
        'western_denomination': fields.char(_('Western denomination')),
        'community_name': fields.char(_('Community name')),
        # Example of a field used for description generation. It should refer
        # to a value in the child.property.value model. This way, we can set
        # dynamic translations and reuse them if multiple projects refer
        # to a same value. Property_name filter is important to give a context
        # to words.
		'closest_city_ids': fields.many2many(
			'compassion.child.property.value', 'project_property_to_value',
			'property_id', 'value_id', _('Closest city'),
			domain=[('property_name', '=', 'closest_city')]),
		'terrain_description_ids': fields.many2many(
			'compassion.child.property.value', 'project_property_to_value',
			'property_id', 'value_id', _('Terrain description'),
			domain=[('property_name', '=', 'terrain_description')]),
		'community_population': fields.integer(_('Community population')),
		'floor_material_ids': fields.many2many(
            'compassion.child.property.value', 'project_property_to_value',
            'property_id', 'value_id', _('Typical floor material'),
            domain=[('property_name', '=', 'floor_material')]),
		'wall_material_ids': fields.many2many(
			'compassion.child.property.value', 'project_property_to_value',
 			'property_id', 'value_id', _('Wall material'),
			domain=[('property_name', '=', 'wall_material')]),
		'roof_material_ids': fields.many2many(
			'compassion.child.property.value', 'project_property_to_value',
 			'property_id', 'value_id', _('Roof material'),
			domain=[('property_name', '=', 'roof_material')]),
		'spoken_languages_ids': fields.many2many(
			'compassion.child.property.value', 'project_property_to_value',
 			'property_id', 'value_id', _('Spoken languages'),
			domain=[('property_name', '=', 'spoken_languages')]),
		'primary_diet_ids': fields.many2many(
            'compassion.child.property.value', 'project_property_to_value',
            'property_id', 'value_id', _('Primary diet'),
            domain=[('property_name', '=', 'primary_diet')]),
        'country_id': fields.many2one('compassion.country', _('Country')),
		'health_problems_ids': fields.many2many(
            'compassion.child.property.value', 'project_property_to_value',
            'property_id', 'value_id', _('Health problem'),
            domain=[('property_name', '=', 'health_problem')]),
		'unemployment_rate': fields.float(_('Unemployment rate')),
		'primary_occupation_ids': fields.many2many(
            'compassion.child.property.value', 'project_property_to_value',
            'property_id', 'value_id', _('Occupation title'),
            domain=[('property_name', '=', 'occupation_title')]),
		'monthly_income': fields.float(_('Monthly income')),
		'economic_needs_ids': fields.many2many(
            'compassion.child.property.value', 'project_property_to_value',
            'property_id', 'value_id', _('Economic needs'),
            domain=[('property_name', '=', 'economic_needs')]),
		'education_needs_ids': fields.many2many(
            'compassion.child.property.value', 'project_property_to_value',
            'property_id', 'value_id', _('Education needs'),
            domain=[('property_name', '=', 'educational_needs')]),
		'social_needs_ids': fields.many2many(
            'compassion.child.property.value', 'project_property_to_value',
            'property_id', 'value_id', _('Social needs'),
            domain=[('property_name', '=', 'social_needs')]),
		'spiritual_needs_ids': fields.many2many(
            'compassion.child.property.value', 'project_property_to_value',
            'property_id', 'value_id', _('Spiritual needs'),
            domain=[('property_name', '=', 'spiritual_needs')]),
		'organization_name': fields.char(_('Organization name')),
	}

    def update_informations(self, cr, uid, ids, context=None):
        ''' Get the most recent informations for selected projects '''
        if not isinstance(ids, list):
            ids = [ids]

        country_obj = self.pool.get('compassion.country')
        ret = {}
        for project in self.browse(cr, uid, ids, context):
            values, country, type, community_id = self._update_program_info(
                cr, uid, project, context)
            v, mv = self._update_community_info(cr, uid, community_id, context)
            values.update(v)
            if type == 'CDSP':
                values.update(self._update_cdsp_info(cr, uid,
                                                     project, context))
            values['primary_diet_ids'] = [(6, 0, mv)]
            country_id = country_obj.search(
                cr, uid, [('iso_code', '=', country)], context=context)
            if not country_id:
                country_id = country_obj.create(
                    cr, uid, {'iso_code': country}, context=context)
                country_obj.update_informations(cr, uid, [country_id],
                                                context=context)
            values['country_id'] = country_id
            self.write(cr, uid, [project.id], values, context=context)

        return True

    def _update_program_info(self, cr, uid, project, context=None):
        url = self._get_url(project.code, 'programimplementor')
        r = requests.get(url)
        if not r.status_code/100 == 2:
            return None

        prog_impl = json.loads(r.text)
        
        values = self._get_program_values(cr, uid, prog_impl, context)
        
        coutry_code = prog_impl.get('ISOCountryCode')
        type = prog_impl.get('ProgramImplementorTypeCode')
        community_id = prog_impl.get('CommunityID')
        return values, coutry_code, type, community_id

    def _update_community_info(self, cr, uid, community_id, context=None):
        url = self._get_url(community_id, 'community')
        r = requests.get(url)
        if not r.status_code/100 == 2:
            return None

        json_data = json.loads(r.text)
        return self._get_community_values(cr, uid, json_data, context)

    def _update_cdsp_info(self, cr, uid, project, context=None):
        url = self._get_url(project.code, 'cdspimplementor')
        r = requests.get(url)
        if not r.status_code/100 == 2:
            return None

        cdsp_impl = json.loads(r.text)
        return self._get_cdsp_values(cr, uid, cdsp_impl, context)

    def _get_program_values(self, cr, uid, json_values, context=None):
        ''' Map JSON values to openERP fields.
            @param self: Python equivalent for "this"
            @param cr: OpenERP database cursor. Used for object browsing
            @param uid: Current user id. Standard parameter.
            @param json_values: json parsed values retrieved from 
                https://api2.compassion.com/ci/v1/programimplementor/ . Please
                look at http://bit.ly/YKrD4d to see full description
            @param context: Standard strategy used in OpenERP to share and set
                default values in the views. This should be part of most
                function signatures
        '''
        values = {}

        # For example, we map a bunch of fields
        json_field_mapping = {
            'ProgramImplementorTypeCode': 'type',
            'OrganizationName': 'local_church_name',
            'HIVCategory': 'hiv_category',
            'MonthSchoolYearBegins': 'month_school_year_begins',
            'CountryDenomination': 'country_denomination',
            'WesternDenomination': 'western_denomination',
            'CommunityName': 'community_name',
            'OrganizationName': 'organization_name',
            }

        # Setup the values dict. In OpenERP object creation/update is made
        # this way: you should give a dict with field_name:value to create or
        # write function. Setting my_object.field_name = value won't work in
        #OpenERP 7
        for json_name, field in json_field_mapping.iteritems():
            if json_values.get(json_name):
                values[field] = json_values[json_name]

        
        # TODO: look at a project description (in web-client). All the
        # informations needed to generate this kind of description comes from
        # one of this web-service : 
        # - REST_Get_Program_Implementor
        # - REST_Get_Community
        # - Get_CDSP_Implementor
        # Your job is to map this infos in the appropriate function:
        # - _get_program_values
        # - _get_community_values
        # - _get_cdsp_values

        return values

    def _get_community_values(self, cr, uid, json_values, context=None):
        ''' Map JSON values to fields.
            REST_Get_Community
        '''
        values = {}

        # Example of a field used for description generation. It should refer
        # to a value in the child.property.value model. This way, we can set
        # dynamic translations and reuse them if multiple projects refer
        # to a same value. Property_name filter is important to give a context
        # to words.
        
        values['unemployment_rate'] = json_values['UnemploymentRate']
        values['community_population'] = json_values['CommunityPopulation']
        values['monthly_income'] = json_values['FamilyMonthlyIncome']

        # dico cle -> nom du champ openerp, value -> tuple contenant le nom du champ json et le separateur 
        # we create a dico
       
        json_misc_tags = {
        'DistanceFromClosestCity': ('closest',','),
        'TerrainDescription': ('terrain_description','/'),
        'TypicalFloorBuildingMaterialDescription': ('floor_material','/'),
        'TypicalWallBuildingMaterialDescription': ('wall_material','/'),
        'TypicalRoofBuildingMaterialDescription': ('roof_material','/'),
        'PrimaryEthnicGroup': ('spoken_languages','/'),
        'PrimaryDiet': ('primary_diet',','),
        'CommonHealthProblems': ('health_problem',','),
        'PrimaryOccupationTitle': ('occupation_title','/'),
        'EconomicNeeds': ('economic_needs',','),
        'EducationalNeeds': ('educational_needs','.'),
        'SocialNeeds': ('social_needs',','),
        'SpiritualNeeds': ('spiritual_needs',','),
        'ClosestCityName': ('closest_city', '***'),
        }
        """
        multi_value = self._get_values(cr, uid,
                                        json_values['DistanceFromClosestCity'].split(','),
                                        'closest_city', context)
        """
        multi_value = []
        for json_key, field_tuple in json_misc_tags.iteritems():
            field_name = field_tuple[0]
            separator = field_tuple[1]
            multi_value.extend(self._get_values(cr, uid,
                                                 json_values[json_key].split(separator),
                                                 field_name, context))
        # Set Many2One or Many2Many values
        

        return values, multi_value

    def _get_cdsp_values(self, cr, uid, json_values, context=None):
        ''' Map JSON values to fields.
            Get_CDSP_Implementor method.
        '''
        values = {}
        json_field_mapping = {
            'Name': 'name',
            'StartDate': 'start_date',
            'StopDate': 'stop_date',
            'LastUpdateDate': 'last_update_date',
            'Status': 'status',
            'StatusDate': 'status_date',
            'StatusComment': 'status_comment',
            'Description': 'description_en',
            'GPSCoordinateLatitudeHighPrecision': 'gps_latitude',
            'GPSCoordinateLongitudeHighPrecision': 'gps_longitude',
            }

        for json_name, field in json_field_mapping.iteritems():
            if json_values.get(json_name):
                values[field] = json_values[json_name]

        return values

    # Same as in child. Should we create a tool class handing this use-case ?
    def _get_values(self, cr, uid, _list, property_name, context):
        value_ids = []
        if isinstance(_list, list):
            for elem in _list:
                value_ids.append(self._get_value_id(cr, uid, elem,
                                                    property_name, context))
        elif isinstance(_list, basestring):
            value_ids.append(self._get_value_id(cr, uid, _list, property_name,
                                                context))
        return value_ids

    def _get_value_id(self, cr, uid, value, property_name, context=None):
        ''' Get id for value having property_name, else create one '''
        prop_val_obj = self.pool.get('compassion.child.property.value')
        value = value.lower()
        val_ids = prop_val_obj.search(cr, uid, [('value_en', '=like', value),
                                                ('property_name', '=', property_name)],
                                      context=context)
        if val_ids:
            return val_ids[0]
        prop_id = prop_val_obj.create(cr, uid, {'property_name': property_name,
                                                'value_en': value})
        return prop_id

    def _get_url(self, project_code, api_mess):
        url = config.get('compass_url')
        api_key = config.get('compass_api_key')
        if not url or not api_key:
            raise orm.except_orm('ConfigError',
                                 _('Missing compass_url or compass_api_key '
                                   'in conf file'))
        if url.endswith('/'):
            url = url[:-1]
        url += '/ci/v1/' + api_mess + '/' + project_code + '?api_key=' + api_key
        return url
