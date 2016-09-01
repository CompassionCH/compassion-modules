# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


def _find_gender(title):
    if title in ('Madam', 'Miss'):
        return 'Female'
    else:
        return 'Male'


class ResPartnerMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field
    names for the model Res Partner.
    """

    ODOO_MODEL = 'res.partner'
    MAPPING_NAME = 'UpsertPartner'

    CONNECT_MAPPING = {
        'GlobalID': 'global_id',
        'GPID': 'ref',
        'Gender': ('title.name', 'res.partner.title'),
        'MandatoryReviewRequired': 'mandatory_review',
        'PreferredName': 'name',
        'CommunicationDeliveryPreference': 'send_original',
        'FirstName': 'firstname',
        'LastName': 'lastname',
    }

    FIELDS_TO_SUBMIT = {
        'Gender': lambda title: _find_gender(title),
        'MandatoryReviewRequired': None,
        'PreferredName': None,
        'CommunicationDeliveryPreference':
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
