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


class BaseSponsorshipMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for the model Sponsorship.

    All fields are described at
    http://developer.compassion.com/docs/read/compassion_connect2/
    Communication_Kit_Fields_and_Sample_JSON
    """
    ODOO_MODEL = 'recurring.contract'
    ACTION = 'default'

    CONNECT_MAPPING = {
        "Commitment_ID": "id",
        "CommitmentEndDate": "end_date",
        "CompassNeedKey": ('child_id.local_id', 'compassion.child'),
        "CorrespondenceEndDate": "end_date",
        "CorrespondentCorrespondenceLanguage": None,
        "CorrespondentSupporterGlobalID": None,
        "FinalCommitmentOfLine": None,
        "HoldID": "reference",
        "HoldType": "type",
        "PrimaryHoldOwner": ('partner_id.name', 'res.partner'),
        "SecondaryHoldOwner": None,
        "SponsorCorrespondenceLanguage": ('reading_language.id',
                                          'res.lang.compassion'),
        "SponsorSupporterGlobalID": ('partner_id.global_id', 'res.partner'),
        "Beneficiary_GlobalID": ('child_id.global_id', 'compassion.child'),
        "Beneficiary_HoldExpirationDate": "end_date",
        "Channel_Name": "channel",
        "LinkType": None,
        "DelinkType": None,
        "ParentCommitmentID": None
    }

    CONSTANTS = {
        "CorrespondentGlobalPartnerID": "CH",
        "IsSponsorCorrespondent": False,
        "SponsorGlobalPartnerID": "CH",
        "FinalCommitmentOfLine": "",
        "GlobalPartner_ID": "CH"
    }
