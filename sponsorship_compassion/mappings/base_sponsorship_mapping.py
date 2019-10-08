##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Michael Sandoz <michaelsandoz87@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping \
    import OnrampMapping
from odoo.addons.child_compassion.models.compassion_hold import \
    HoldType


class BaseSponsorshipMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for the model Sponsorship.

    All fields are described at
    http://developer.compassion.com/docs/read/compassion_connect2/
    Communication_Kit_Fields_and_Sample_JSON
    """
    ODOO_MODEL = 'recurring.contract'
    MAPPING_NAME = 'default'

    CONNECT_MAPPING = {
        "Commitment_ID": "global_id",
        "CommitmentID": "global_id",
        "CommitmentEndDate": "end_date",
        "CompassNeedKey": ('child_id.local_id', 'compassion.child'),
        "CorrespondenceEndDate": "end_date",
        "CorrespondentCorrespondenceLanguage": None,
        "CorrespondentSupporterGlobalID": None,
        "FinalCommitmentOfLine": None,
        "HoldID": None,
        "HoldType": None,
        "PrimaryHoldOwner": ('write_uid.name', 'res.users'),
        "SecondaryHoldOwner": ('create_uid.name', 'res.users'),
        "SponsorCorrespondenceLanguage": ('reading_language.name',
                                          'res.lang.compassion'),
        "SponsorSupporterGlobalID": ('correspondent_id.global_id',
                                     'res.partner'),
        "Beneficiary_GlobalID": ('child_id.global_id', 'compassion.child'),
        "HoldExpirationDate": "hold_expiration_date",
        "Channel_Name": None,
        "LinkType": None,
        "DelinkType": None,
        "ParentCommitmentID": ('parent_id.global_id', 'recurring.contract'),
    }

    CONSTANTS = {
        "CorrespondentGlobalPartnerID": "CH",
        "IsSponsorCorrespondent": True,
        "SponsorGlobalPartnerID": "CH",
        "FinalCommitmentOfLine": "",
        "GlobalPartner_ID": "CH",
        "HoldType": HoldType.SPONSOR_CANCEL_HOLD.value,
        "DelinkType": "Sponsor-requested Cancellation",
    }
