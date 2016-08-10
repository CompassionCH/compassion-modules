# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping
from datetime import datetime


class ProjetReservationCreateMapping(OnrampMapping):
    """
    Project reservation mapping for the create operation
    """
    ODOO_MODEL = 'icp.reservation'
    MAPPING_NAME = "create_reservation"

    CONNECT_MAPPING = {
        'Beneficiary_GlobalID': 'global_id',
        'Channel_Name': 'channel_name',
        'ICP_ID': ('icp_id.icp_id', 'compassion.project'),
        'CampaignEventIdentifier': 'campaign_event_identifier',
        'ExpirationDate': 'expiration_date',
        'HoldExpirationDate': 'hold_expiration_date',
        'HoldYieldRate': 'hold_yield_rate',
        'ID': 'reservation_id',
        'IsReservationAutoApproved': 'is_reservation_auto_approved',
        'NumberOfBeneficiaries': 'number_of_beneficiaries',
        'PrimaryOwner': 'primary_owner',
        'SecondaryOwner': 'secondary_owner',
        'Reservation_ID': 'reservation_id',
    }

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

        """ Don't send fields not set. """
        temp_data = connect_data.copy()
        for key, value in temp_data.iteritems():
            if not value:
                del connect_data[key]


class ProjetReservationCancelMapping(ProjetReservationCreateMapping):
    """
        Project reservation mapping for the cancel operation
    """
    MAPPING_NAME = "cancel_reservation"

    FIELDS_TO_SUBMIT = {
        'GlobalPartner_ID': 'CH',
        'Reservation_ID': None,
    }
