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
        #'country_id': fields.many2one('compassion.country', _('Country')),
    }

    def update_informations(self, cr, uid, ids, context=None):
        ''' Get the most recent informations for selected projects '''
        if not isinstance(ids, list):
            ids = [ids]

        ret = {}
        for project in self.browse(cr, uid, ids, context):
            coutry, type = self._update_program_info(cr, uid, project, context)
            if type == 'CDSP':
                self._update_cdsp_info(cr, uid, project, context)

        #TODO: Update related country informations
        return True

    def _update_program_info(self, cr, uid, project, context=None):
        url = self._get_url(project.code, 'programimplementor')
        r = requests.get(url)
        if not r.status_code/100 == 2:
            return None

        prog_impl = json.loads(r.text)
        values = {}
        json_field_mapping = {
            'ProgramImplementorTypeCode': 'type',
            'OrganizationName': 'local_church_name',
            'HIVCategory': 'hiv_category',
            'MonthSchoolYearBegins': 'month_school_year_begins',
            'CountryDenomination': 'country_denomination',
            'WesternDenomination': 'western_denomination',
            'CommunityName': 'community_name',
            }

        for json_name, field in json_field_mapping.iteritems():
            if prog_impl.get(json_name):
                values[field] = prog_impl[json_name]
        self.write(cr, uid, [project.id], values, context=context)
        coutry_code = prog_impl.get('ISOCountryCode')
        type = prog_impl.get('ProgramImplementorTypeCode')
        return coutry_code, type

    def _update_cdsp_info(self, cr, uid, project, context=None):
        url = self._get_url(project.code, 'cdspimplementor')
        r = requests.get(url)
        if not r.status_code/100 == 2:
            return None

        cdsp_impl = json.loads(r.text)
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
            if cdsp_impl.get(json_name):
                values[field] = cdsp_impl[json_name]

        self.write(cr, uid, [project.id], values, context=context)

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
