# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Michael Sandoz <sandozmichael@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping
from datetime import datetime

_logger = logging.getLogger(__name__)


class ChilpoolCreateHoldMapping(OnrampMapping):
    """
    Childpool mapping for reserving available children from GMC.
    """
    ODOO_MODEL = 'compassion.hold'
    MAPPING_NAME = "create_hold"

    CONNECT_MAPPING = {
        'Beneficiary_GlobalID': ('child_id.global_id', 'compassion.child'),
        "BeneficiaryState": 'type',
        'EstimatedNoMoneyYieldRate': 'no_money_yield_rate',
        'HoldEndDate': 'expiration_date',
        "HoldID": 'hold_id',
        'HoldYieldRate': 'yield_rate',
        'PrimaryHoldOwner': 'primary_owner.name',
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
        "SourceCode": lambda s: '65-' + s if s else '',
        'Channel_Name': None,
        "GlobalPartner_ID": None,
    }

    CONSTANTS = {
        "GlobalPartner_ID": "CH",
        "IsSpecialHandling": False,
    }

    def _process_connect_data(self, connect_data):
        # Set end date to correct format for Connect
        endDateStr = connect_data.get('HoldEndDate')
        if endDateStr:
            endDate = datetime.strptime(endDateStr, "%Y-%m-%d %H:%M:%S")
            connect_data['HoldEndDate'] = endDate.strftime(
                "%Y-%m-%dT%H:%M:%SZ")
        for key, val in connect_data.copy().iteritems():
            if not val:
                del connect_data[key]

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """
        Don't update Hold Owner and avoid security restrictions if
        owner is in another company.
        """
        if connect_name == 'PrimaryHoldOwner':
            return {}
        return super(ChilpoolCreateHoldMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search)

    def get_connect_data(self, odoo_object, fields_to_submit=None):
        """
        Prevents security restrictions to get the Primary Owner name
        in case the user that made the hold is in another Company.
        """
        if fields_to_submit is None:
            fields_to_submit = self.FIELDS_TO_SUBMIT.keys()
        try:
            fields_to_submit.remove('PrimaryHoldOwner')
        except ValueError:
            _logger.warning('No primary owner for hold mapping')
        res = super(ChilpoolCreateHoldMapping, self).get_connect_data(
            odoo_object, fields_to_submit)
        res['PrimaryHoldOwner'] = odoo_object.sudo().primary_owner.name
        return res


class ChilpoolReleaseHoldMapping(ChilpoolCreateHoldMapping):
    """
        Childpool mapping for realease children on GMC.
        """
    MAPPING_NAME = "release_hold"

    FIELDS_TO_SUBMIT = {
        'Beneficiary_GlobalID': None,
        "HoldID": None,
        "GlobalPartner_ID": None,
    }


class ReservationToHoldMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.hold'
    MAPPING_NAME = 'reservation_to_hold'

    CONNECT_MAPPING = {
        'HoldID': 'hold_id',
        'Beneficiary_GlobalID': ('child_id.global_id', 'compassion.child'),
        'HoldExpirationDate': 'expiration_date',
        'PrimaryOwner': ('primary_owner.name', 'res.users'),
        'ReservationHoldType': 'type',
        'ReservationID': ('reservation_id.reservation_id',
                          'compassion.reservation'),
        'SecondaryOwner': 'secondary_owner',
        # Not used in Odoo
        'BeneficiaryOrder_ID': None,
        'GlobalPartner_ID': None,
        'ICP_ID': None,
        'ReservationType_Name': None,
        'CampaignEventID': None,
    }

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """
        Don't update Hold Owner and avoid security restrictions if
        owner is in another company.
        """
        if connect_name == 'PrimaryOwner':
            return {}
        return super(ReservationToHoldMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search)

    def get_connect_data(self, odoo_object, fields_to_submit=None):
        """
        Prevents security restrictions to get the Primary Owner name
        in case the user that made the hold is in another Company.
        """
        if fields_to_submit is None:
            fields_to_submit = self.FIELDS_TO_SUBMIT.keys()
        try:
            fields_to_submit.remove('PrimaryOwner')
        except ValueError:
            _logger.warning('No primary owner for reservation mapping')
        res = super(ReservationToHoldMapping, self).get_connect_data(
            odoo_object, fields_to_submit)
        res['PrimaryOwner'] = odoo_object.sudo().primary_owner.name
        return res
