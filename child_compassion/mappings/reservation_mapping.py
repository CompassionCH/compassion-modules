# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping
from datetime import datetime

_logger = logging.getLogger(__name__)


class ReservationCreateMapping(OnrampMapping):
    """
    Project reservation mapping for the create operation
    """
    ODOO_MODEL = 'compassion.reservation'
    MAPPING_NAME = "create_reservation"

    CONNECT_MAPPING = {
        'Beneficiary_GlobalID': 'child_global_id',
        'Channel_Name': 'channel',
        'ICP_ID': ('fcp_id.fcp_id', 'compassion.project'),
        'CampaignEventIdentifier': ('fcp_id.fcp_id', 'compassion.project'),
        'ExpirationDate': 'reservation_expiration_date',
        'HoldExpirationDate': 'expiration_date',
        'HoldYieldRate': 'yield_rate',
        'ID': 'reservation_id',
        'IsReservationAutoApproved': 'is_reservation_auto_approved',
        'NumberOfBeneficiaries': 'number_of_beneficiaries',
        'PrimaryOwner': 'primary_owner.name',
        'SecondaryOwner': 'secondary_owner',
        'Reservation_ID': 'reservation_id',
    }

    FIELDS_TO_SUBMIT = {
        'Channel_Name': None,
        'GlobalPartner_ID': None,
        'ICP_ID': None,
        'CampaignEventIdentifier': lambda x: x or 'Child reservation',
        'ExpirationDate': None,
        'HoldExpirationDate': None,
        'HoldYieldRate': None,
        'ID': None,
        'IsReservationAutoApproved': None,
        'NumberOfBeneficiaries': None,
        'PrimaryOwner': None,
        'ReservationType': None,
        'SecondaryOwner': None,
        'SourceCode': None,
    }

    CONSTANTS = {
        'GlobalPartner_ID': 'CH',
        'ReservationType': 'ICP',
        'SourceCode': '',
    }

    def _process_connect_data(self, connect_data):
        # Set expiration date to correct format for Connect
        if 'HoldExpirationDate' in connect_data:
            expirationDateStr = connect_data.get('HoldExpirationDate')
            expirationDate = datetime.strptime(expirationDateStr,
                                               "%Y-%m-%d %H:%M:%S")
            connect_data['HoldExpirationDate'] = expirationDate.strftime(
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
        if connect_name == 'PrimaryOwner':
            return {}
        return super(ReservationCreateMapping, self)._convert_connect_data(
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
        res = super(ReservationCreateMapping, self).get_connect_data(
            odoo_object, fields_to_submit)
        res['PrimaryOwner'] = odoo_object.sudo().primary_owner.name


class ProjetReservationCancelMapping(ReservationCreateMapping):
    """
        Project reservation mapping for the cancel operation
    """
    MAPPING_NAME = "cancel_reservation"

    FIELDS_TO_SUBMIT = {
        'GlobalPartner_ID': 'CH',
        'Reservation_ID': None,
    }


class BeneficiaryReservationMapping(ReservationCreateMapping):
    """
        Project reservation mapping for the beneficiary reservation operation
    """
    MAPPING_NAME = "beneficiary_reservation"

    FIELDS_TO_SUBMIT = {
        'Beneficiary_GlobalID': None,
        'Channel_Name': None,
        'GlobalPartner_ID': None,
        'ICP_ID': None,
        'CampaignEventIdentifier': None,
        'ExpirationDate': None,
        'HoldExpirationDate': None,
        'HoldYieldRate': None,
        'ID': None,
        'IsReservationAutoApproved': None,
        'NumberOfBeneficiaries': None,
        'PrimaryOwner': None,
        'ReservationType': None,
        'SecondaryOwner': None,
        'SourceCode': None,
    }

    CONSTANTS = {
        'GlobalPartner_ID': 'CH',
        'ReservationType': 'Sponsorship Beneficiary',
        'SourceCode': '',
        'CampaignEventIdentifier': 'Child reservation',
    }
