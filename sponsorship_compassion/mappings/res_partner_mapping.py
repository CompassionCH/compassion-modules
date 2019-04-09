# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class ResPartnerMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field
    names for the model Res Partner.
    """

    ODOO_MODEL = 'res.partner'
    MAPPING_NAME = 'UpsertPartner'

    CONNECT_MAPPING = {
        'GlobalID': 'global_id',
        'GPID': 'ref',
        'Gender': ('title', 'res.partner.title'),
        'MandatoryReviewRequired': 'mandatory_review',
        'PreferredName': 'preferred_name',
        'CorrespondenceDeliveryPreference': 'send_original',
        'FirstName': 'firstname',
        'LastName': 'lastname',
    }

    FIELDS_TO_SUBMIT = {
        'Gender': lambda title:
            title.gender if title.with_context(lang='en_US').name in
            ['Mister', 'Madam', 'Misters', 'Ladies'] else None,
        'MandatoryReviewRequired': None,
        'PreferredName': None,
        'CorrespondenceDeliveryPreference':
            lambda original: 'Physical' if original else 'Digital',
        'GlobalPartner': None,
        'GPID': lambda ref: '65-' + ref,
        'FirstName': None,
        'LastName': None,
        'Status': None,
        'GlobalID': None,
    }

    CONSTANTS = {
        "GlobalPartner": "Compassion Switzerland",
        "Status": "Active",
    }

    def _process_connect_data(self, connect_data):
        """Don't send GlobalID if not set."""
        if not connect_data.get('GlobalID') and 'GlobalID' in connect_data:
            del connect_data['GlobalID']

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """ Remove 65- suffix from partner reference
        """
        if connect_name == 'GPID':
            value = value[3:]
        return super(ResPartnerMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search)


class AnonymizePartner(OnrampMapping):
    ODOO_MODEL = 'res.partner'
    MAPPING_NAME = 'AnonymizePartner'

    CONNECT_MAPPING = {
        'GlobalSupporterID': 'global_id',
        'GP_SupporterID': 'ref',
    }

    FIELDS_TO_SUBMIT = {
        'GlobalSupporterID': None,
        'GP_SupporterID': lambda ref: '65-' + ref,
        'GP_ID': None,
        'DataProtection_Type': None
    }

    CONSTANTS = {
        "GP_ID": "CH",
        "DataProtection_Type": "ForgetMe"
    }
