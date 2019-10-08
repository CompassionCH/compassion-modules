##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Michael Sandoz <michaelsandoz87@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from .base_sponsorship_mapping import BaseSponsorshipMapping


class CreateSponsorship(BaseSponsorshipMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for the model Sponsorship.

    All fields are described at
    http://developer.compassion.com/docs/read/compassion_connect2/
    Communication_Kit_Fields_and_Sample_JSON
    """
    MAPPING_NAME = 'CreateSponsorship'

    FIELDS_TO_SUBMIT = {
        "HoldID": None,
        "IsSponsorCorrespondent": None,
        "PrimaryHoldOwner": None,
        "SponsorGlobalPartnerID": None,
        "SponsorSupporterGlobalID": None,
        "SponsorCorrespondenceLanguage": None,
        "Beneficiary_GlobalID": None,
        "CommitmentID": None,
        "ParentCommitmentID": lambda parent: parent or None,
    }

    def __init__(self, env):
        super().__init__(env)
        self.CONNECT_MAPPING['HoldID'] = ('child_id.hold_id.hold_id',
                                          'compassion.child')

    def _process_connect_data(self, connect_data):
        # Don't send global id if not set.
        if not connect_data.get('GlobalId') and 'GlobalId' in connect_data:
            del connect_data['GlobalId']
