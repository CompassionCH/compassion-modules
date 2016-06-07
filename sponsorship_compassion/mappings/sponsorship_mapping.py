# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Michael Sandoz <michaelsandoz87@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.addons.message_center_compassion.mappings.base_mapping \
    import OnrampMapping

import logging
logger = logging.getLogger(__name__)


class SponsorshipMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for the model Sponsorship.

    All fields are described at
    http://developer.compassion.com/docs/read/compassion_connect2/
    Communication_Kit_Fields_and_Sample_JSON
    """
    ODOO_MODEL = 'recurring.contract'

    CONNECT_MAPPING = {
        "CommitmentEndDate": "end_date",
        "CompassNeedKey": ('child_id.local_id', 'compassion.child'),
        "CorrespondenceEndDate": "end_date",
        "CorrespondentCorrespondenceLanguage": None,
        "CorrespondentSupporterGlobalID": None,
        "FinalCommitmentOfLine": None,
        "HoldID": "reference",
        "PrimaryHoldOwner": ('partner_id.name', 'res.partner'),
        "SecondaryHoldOwner": None,
        "SponsorCorrespondenceLanguage": ('reading_language.id',
                                          'res.lang.compassion'),
        "SponsorSupporterGlobalID": ('partner_id.global_id', 'res.partner'),
        "Beneficiary_GlobalID": ('child_id.global_id', 'compassion.child'),
        "Channel_Name": "channel",
        "LinkType": None,
        "ParentCommitmentID": None
    }

    FIELDS_TO_SUBMIT = {
        "HoldID": None,
        "IsSponsorCorrespondent": None,
        "PrimaryHoldOwner": None,
        "SponsorGlobalPartnerID": None,
        "SponsorSupporterGlobalID": None,
        "Beneficiary_GlobalID": None
    }

    CONSTANTS = {
        "CorrespondentGlobalPartnerID": "CH",
        "IsSponsorCorrespondent": False,
        "SponsorGlobalPartnerID": "CH"
    }

    def _process_connect_data(self, odoo_data):
        # Don't send global id if not set.
        if not odoo_data.get('GlobalId') and 'GlobalId' in odoo_data:
            del odoo_data['GlobalId']
