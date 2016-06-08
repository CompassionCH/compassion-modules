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


class CancelSponsorship(BaseSponsorshipMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for delete a sponsorship.
    """

    ACTION = 'CancelSponsorship'

    FIELDS_TO_SUBMIT = {
        "FinalCommitmentOfLine": None,
        "Beneficiary_GlobalID": None,
        "Beneficiary_HoldExpirationDate": None,
        "Commitment_ID": None,
        "SponsorSupporterGlobalID": None,
        "GlobalPartner_ID": None,
        "SponsorSupporterGlobalID": None,
        "HoldType": None
    }
