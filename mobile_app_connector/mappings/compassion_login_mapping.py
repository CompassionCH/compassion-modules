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


class MobileLoginMapping(OnrampMapping):
    ODOO_MODEL = 'res.users'
    MAPPING_NAME = 'mobile_app_login'

    CONNECT_MAPPING = {
        'userid': 'id',
        'titleid': ('title.name', 'res.partner.title'),
        'firstname': 'firstname',
        'lastname': 'lastname',
        'yearofbirth': 'birthdate',
        'email': 'email',
        'screenname': None,
        'twitterid': None,
        'username': 'login',
        'password': 'password',
        'status': None,
        'contactid': ('partner_id.id', 'res.partner'),
        'activation': None,
        'alternateemail1': None,
        'alternateemail2': None,
        'homephone': 'phone',
        'mobilephone': 'mobile',
        'officephone': None,
        'street1': 'street',
        'street2': 'street2',
        'street3': None,
        'street4': None,
        'street5': None,
        'town': 'city',
        'county': ('state_id.id', 'res.country.state'),
        'postcode': 'zip',
        'country': ('country_id.id', 'res.country'),
        'receive_emails': None,  # ?
        'no_emails': None,  # ?
        'photo': 'image',
        'sponsorshipplus_flag': None,  # ?
        'fb_login': None,
        'dd_flag': None,
        'bb_dd_flag': None,
        'login_count': 'login_date',
        'last_login_time': 'login_date',
        'createdTime': 'create_date',
        'error': None
    }

    FIELDS_TO_SUBMIT = {k: None for k, v in CONNECT_MAPPING.iteritems() if v}

    # override get_connect_data to compute value for field 'login_count'
    def get_connect_data(self, odoo_object, fields_to_submit=None):
        mapped = super(MobileLoginMapping, self).get_connect_data(
            odoo_object, fields_to_submit)
        mapped['login_count'] = len(odoo_object.log_ids)
        return mapped
