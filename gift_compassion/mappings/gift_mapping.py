# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.addons.message_center_compassion.mappings.base_mapping \
    import OnrampMapping


class CreateGiftMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field
    names for the model Res Gift.
    """

    ODOO_MODEL = 'sponsorship.gift'

    CONNECT_MAPPING = {
        'Beneficiary_GlobalID': ('child_id.global_id', 'compassion.child'),
        'AmountInOriginatingCurrency': 'amount',
        'GiftSubType': 'sponsorship_gift_type',
        'GiftType': 'attribution',
        'GlobalPartnerNote': 'instructions',
        'PartnerGiftDate': 'date_partner_paid',
        'PartnerGiftID': 'id',
        'RecipientID': ('child_id.local_id', 'compassion.child'),
        'RecipientType': 'gift_type',
        'Supporter_GlobalID': ('partner_id.global_id', 'res.partner'),
        'ExchangeRatePartnerToGMC': None,
        'Id': 'gmc_gift_id',
        'ThresholdViolatedType': None,
        'IsThresholdViolated': 'threshold_alert',
        'GiftDeliveryStatus': 'gmc_state',
        'ID': 'gmc_gift_id',
        'StatusChangeDate': None,
        'UndeliverableReason': 'undeliverable_reason',
    }

    FIELDS_TO_SUBMIT = {
        'Beneficiary_GlobalID': None,
        'AmountInOriginatingCurrency': None,
        'GiftSubType': None,
        'GiftType': None,
        'GlobalPartnerNote': None,
        'PartnerGiftDate': None,
        'PartnerGiftID': str,
        'RecipientID': None,
        'RecipientType': None,
        'Supporter_GlobalID': None,
        'Supporter_GlobalPartnerSupporterID': None,
        'CurrencyCode': None,
    }

    CONSTANTS = {
        'CurrencyCode': 'CHF',
        'Supporter_GlobalPartnerSupporterID': 'CH',
    }

    def _process_odoo_data(self, odoo_data):
        if 'id' in odoo_data:
            odoo_data['id'] = int(odoo_data['id'])
