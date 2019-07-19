# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import datetime
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class MobileChildMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.child'
    MAPPING_NAME = 'mobile_app_child'

    CONNECT_MAPPING = {
        'Age': 'age',
        'benData': None,
        'BeneficiaryGlobalId': 'global_id',
        'bio': 'desc_en',
        'BirthDate': 'birthdate',
        'Id': 'id',
        'Latitude': ('project_id.gps_latitude', 'compassion.project'),
        'Longitude': ('project_id.gps_longitude', 'compassion.project'),
        'NeedId': 'id',
        'NeedKey': 'local_id',
        'ChildNeedKey': 'local_id',
        'CommunityDescription': None,
        'Country': ('project_id.country_id.name', 'res.country'),
        'CountryCode': ('project_id.country_id.code', 'res.country'),
        'directdebitflag': None,
        'Email': None,
        'FirstName': 'firstname',
        'FullBodyImageURL': 'image_url',
        'FullName': 'name',
        'Gender': 'gender',
        'IcpId': ('project_id.fcp_id', 'compassion.project'),
        'image': None,
        'ImageUrl': 'image_url',
        'ImageURL': 'image_url',
        'Name': 'preferred_name',
        'PreferredName': 'preferred_name',
        'ProjectName': ('project_id.name', 'compassion.project'),
        'sponsorBBID': None,
        'sponsorYearOfBirth': None,
        'sponsorshipplusflag': None,
        'SupporterGroupId': ('sponsor_id.id', 'res.partner'),
        'SupporterId': ('sponsor_id.id', 'res.partner'),
        'SupporterName': ('sponsor_id.name', 'res.partner'),
        'timeTaken': None,
        'UpdatedpreferredName': ('sponsor_id.preferred_name', 'res.partner'),
    }

    FIELDS_TO_SUBMIT = {k: None for k, v in CONNECT_MAPPING.iteritems() if v}

    def get_connect_data(self, odoo_object, fields_to_submit=None):
        res = super(MobileChildMapping, self).get_connect_data(
            odoo_object, fields_to_submit)
        if res['FullBodyImageURL']:
            image_url = self.env['child.pictures.download.wizard']\
                .get_picture_url(res['FullBodyImageURL'], 'headshot', 300, 300)
            res['ImageUrl'] = image_url
            res['ImageURL'] = image_url
        return res

    def _process_connect_data(self, connect_data):
        for key, value in connect_data.copy().iteritems():
            if key == "BirthDate":
                if value:
                    connect_data[key] = datetime.datetime.strptime(
                        value, '%Y-%m-%d').strftime('%d/%m/%Y %H:%M:%S')
            if key == "SupporterGroupId":
                if value:
                    connect_data[key] = int(value)
        return connect_data
