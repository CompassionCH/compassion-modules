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


class ResPartnerMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field
    names for the model Res Partner.
    """

    ODOO_MODEL = 'res.partner'

    CONNECT_MAPPING = {
        'GlobalId': 'ref',
        'Gender': ('title.name', 'res.partner.title'),
        'MandatoryReviewRequired': 'mandatory_review',
        'PreferredName': 'name',
        'CommunicationDeliveryPreference': 'send_original',
    }

    FIELDS_TO_SUBMIT = {
        'GlobalId': lambda ref: '65-' + ref,
        'Gender': lambda gen: 'Female' if gen in ('Madam', 'Miss') else
        'Mister',
        'MandatoryReviewRequired': None,
        'PreferredName': None,
        'CommunicationDeliveryPreference': lambda
            original: 'Physical Original Document' if original else
        "Printed Digital Document",

        "GlobalPartner": "Australia",
        "FirstName": "a",
        # "GlobalId": "a",
        "GPID": "AU",
        "LastName": "a",
        "Status": "Active",
        "StatusReason": "Account Merge"
    }

    CONSTANTS = {
        # TODO Update with GMC need data
        "GlobalPartner": "Australia",
        "FirstName": "a",
        # "GlobalId": "a",
        "GPID": "AU",
        "LastName": "a",
        "Status": "Active",
        "StatusReason": "Account Merge"
    }
