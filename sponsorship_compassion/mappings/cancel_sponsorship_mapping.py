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


class CorrespondenceMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for delete a sponsorship.

    All fields are described at
    http://developer.compassion.com/docs/read/compassion_connect2/
    Communication_Kit_Fields_and_Sample_JSON
    """
    ODOO_MODEL = 'recurring.contract'

    CONNECT_MAPPING = {
        "FinalCommitmentOfLine": None,
        "Beneficiary_GlobalID": ('child_id.local_id', 'compassion.child'),
        "Beneficiary_HoldExpirationDate": "end_date",
        "Commitment_ID": "id",
        "PrimaryHoldOwner": ('partner_id.name', 'res.partner'),
        "SecondaryHoldOwner": None,
        "SponsorSupporterGlobalID": ('partner_id.global_id', 'res.partner'),
        "DelinkType": None,
        "HoldType": "type"
    }

    FIELDS_TO_SUBMIT = {
        "FinalCommitmentOfLine": None,
        "Beneficiary_GlobalID": None,
        "Beneficiary_HoldExpirationDate": None,
        "Commitment_ID": None,
        "SponsorSupporterGlobalID": None,
        "GlobalPartner_ID": None,
        "SponsorSupporterGlobalID": None,
        "Holdtype": None
    }

    CONSTANTS = {
        "GlobalPartner_ID": "CH"
    }
