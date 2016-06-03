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
    elif title in ('Mister', 'Sir', 'Doctor', 'Pastor'):
        return 'Male'
    else:
        'Unknown'


class ResPartnerMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field
    names for the model Res Partner.
    """

    ODOO_MODEL = 'res.partner'

    CONNECT_MAPPING = {
        'GlobalId': 'global_id',
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
            lambda original: 'Physical Original Document' if original else
            "Printed Digital Document",
        "GlobalPartner": None,
        "GPID": lambda ref: '65-' + ref,
        "FirstName": None,
        "LastName": None,
        "Status": None
    }

    CONSTANTS = {
        "GlobalPartner": "Switzerland",
        "Status": "Active",
    }

    def _process_connect_data(self, odoo_data):
        # Don't send global id if not set.
        if not odoo_data.get('GlobalId') and 'GlobalId' in odoo_data:
            del odoo_data['GlobalId']

        # Put message inside SupporterProfile tag
        c_odoo_data = odoo_data.copy()
        odoo_data.clear()
        odoo_data.update({'SupporterProfile': [c_odoo_data]})
