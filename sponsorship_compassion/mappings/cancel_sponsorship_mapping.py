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
from base_sponsorship_mapping import BaseSponsorshipMapping
from datetime import datetime


class CancelSponsorship(BaseSponsorshipMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for delete a sponsorship.
    """

    MAPPING_NAME = 'CancelSponsorship'

    FIELDS_TO_SUBMIT = {
        "FinalCommitmentOfLine": None,
        "Beneficiary_GlobalID": None,
        "HoldExpirationDate": None,
        "Commitment_ID": None,
        "SponsorSupporterGlobalID": None,
        "GlobalPartner_ID": None,
        "HoldType": None,
        "PrimaryHoldOwner": None
    }

    def _process_connect_data(self, connect_data):
        # Set end date to correct format for Connect
        if 'HoldExpirationDate' in connect_data:
            endDateStr = connect_data.get('HoldExpirationDate')
            endDate = datetime.strptime(endDateStr, "%Y-%m-%d %H:%M:%S")
            connect_data['HoldExpirationDate'] = endDate.strftime(
                "%Y-%m-%dT%H:%M:%SZ")
