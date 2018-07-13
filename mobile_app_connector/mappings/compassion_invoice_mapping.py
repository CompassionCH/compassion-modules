# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class MobileInvoiceMapping(OnrampMapping):
    ODOO_MODEL = 'amount.invoice'
    MAPPING_NAME = 'mobile_app_correspondence'

    CONNECT_MAPPING = {
        'appealtype': None,
        'appealtypetext': None,
        'appealamount': None,
        'gifttype': None,
        'gifttypetext': None,
        'giftamount': None,
        'childname': None,
        'startmonth': None,
        'startyear': None,
        'endmonth': None,
        'endyear': None,
        'email': None,
        'street1': None,
        'street2': None,
        'street3': None,
        'street4': None,
        'street5': None,
        'town': None,
        'Country': None,
        'postal': None,
        'postcode': None,
        'country': None,
        'support': ('partner.id.id', 'res.partner'),
        'supportergroup': None,
        'epqdreference': None,
        'need': None,
        'LastInsertedDonationId': None,
        'LastInsertedGiftId': None
    }
