##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Michael Sandoz <michaelsandoz87@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields
from .base_sponsorship_mapping import BaseSponsorshipMapping
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
        "DelinkType": None,
        "PrimaryHoldOwner": None
    }

    def __init__(self, env):
        super().__init__(env)
        self.CONNECT_MAPPING['HoldID'] = 'hold_id'

    def _process_connect_data(self, connect_data):
        # Set end date to correct format for Connect
        end_date_str = connect_data.get(
            'HoldExpirationDate') or fields.Datetime.now()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
        connect_data['HoldExpirationDate'] = end_date.strftime(
            "%Y-%m-%dT%H:%M:%SZ")
