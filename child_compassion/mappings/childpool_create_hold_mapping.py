# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Michael Sandoz <sandozmichael@hotmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping
from datetime import datetime


class ChilpoolCreateHoldMapping(OnrampMapping):
    """
    Childpool mapping for searching available children from GMC.
    """
    ODOO_MODEL = 'compassion.hold'
    ACTION = "create_hold"

    CONNECT_MAPPING = {
        # Fields used in Search Message (for global child)
        'Beneficiary_GlobalID': ('child_id.global_id', 'compassion.child'),
        "BeneficiaryState": 'type',
        'EstimatedNoMoneyYieldRate': 'no_money_yield_rate',
        'HoldEndDate': 'expiration_date',
        "HoldID": 'hold_id',
        'HoldYieldRate': 'yield_rate',
        'PrimaryHoldOwner': 'primary_owner',
        'SecondaryHoldOwner': 'secondary_owner',
        "SourceCode": 'source_code',
        'Channel_Name': 'channel',
    }

    FIELDS_TO_SUBMIT = {
        'Beneficiary_GlobalID': None,
        'BeneficiaryState': None,
        'EstimatedNoMoneyYieldRate': None,
        'HoldEndDate': None,
        "HoldID": None,
        'HoldYieldRate': None,
        "IsSpecialHandling": None,
        'PrimaryHoldOwner': None,
        'SecondaryHoldOwner': None,
        "SourceCode": None,
        'Channel_Name': None,
        "GlobalPartner_ID": None,
    }

    CONSTANTS = {
        "GlobalPartner_ID": "CH",
        "IsSpecialHandling": False,
    }

    def _process_connect_data(self, connect_data):
        # Set end date to correct format for Connect
        if 'HoldEndDate' in connect_data:
            endDateStr = connect_data.get('HoldEndDate')
            endDate = datetime.strptime(endDateStr, "%Y-%m-%d %H:%M:%S")
            connect_data['HoldEndDate'] = endDate.strftime(
                "%Y-%m-%dT%H:%M:%SZ")
