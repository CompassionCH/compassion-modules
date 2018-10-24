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
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class MobileChildMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.child'
    MAPPING_NAME = 'mobile_app_child'

    CONNECT_MAPPING = {
        'age': 'age',
        'benData': None,
        'beneficiaryGlobalID': 'global_id',
        'bio': 'desc_en',
        'Birthdate': 'birthdate',
        'childNeedkey': 'local_id',
        'CommunityDescription': None,
        'country': ('project_id.country_id.name', 'res.country'),
        'countryId': ('project_id.country_id.id', 'res.country'),
        'directdebitflag': None,
        'Email': None,
        'FirstName': 'firstname',
        'FullBodyImageURL': 'image_url',
        'FullName': 'name',
        'Gender': 'gender',
        'fcpId': ('project_id.fcp_id', 'compassion.project'),
        'image': None,
        'ImageURL': 'image_url',
        'Latitude': None,
        'Longitude': None,
        'NeedID': 'local_id',
        'preferredName': 'preferred_name',
        'ProjectName': ('project_id.name', 'compassion.project'),
        'sponsorBBID': None,
        'sponsorYearOfBirth': None,
        'sponsorshipplusflag': None,
        'SupportergroupID': None,
        'Supporterid': ('partner_id.global_id', 'res.partner'),
        'Supportername': ('partner_id.name', 'res.partner'),
        'timeTaken': None,
        'UpdatedpreferredName': ('partner_id.preferred_name', 'res.partner')
    }

    FIELDS_TO_SUBMIT = {k: None for k, v in CONNECT_MAPPING.iteritems() if v}
