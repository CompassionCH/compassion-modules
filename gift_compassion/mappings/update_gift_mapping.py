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

from openerp.addons.message_center_compassion.mappings.base_mapping import OnrampMapping


class UpdateGiftMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field
    names for the model Res Gift.
    """

    ODOO_MODEL = 'sponsorship.gift'
    MAPPING_NAME = 'UpdateGift'

    CONNECT_MAPPING = {
        'FieldOfficeNoteFieldForGlobalPartner': 'instructions',
        'GiftDeliveryStatus': 'gmc_state',
        'GlobalPartnerNote': 'instructions',    # ???
        'ID': 'gmc_gift_id',        # ???
        'PartnerGiftID': 'gmc_gift_id',     # ???
        'StatusChangeDate': '',
        'UndeliverableReason': 'undeliverable_reason',
    }

    FIELDS_TO_SUBMIT = {
        'FieldOfficeNoteFieldForGlobalPartner': None,
        'GiftDeliveryStatus': None,
        'GlobalPartnerNote': None,
        'ID': None,
        'PartnerGiftID': None,
        'StatusChangeDate': None,
        'UndeliverableReason': None,
    }