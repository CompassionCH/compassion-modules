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
        'screenname': 'preferred_name',
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

    CONSTANTS = {
        'error': '0',
        'status': '1',
        'activation': '1',
        'alternateemail1': '1',
        'alternateemail2': '1',
        'officephone': '1',
        'street3': '1',
        'street4': '1',
        'street5': '1',
        'twitterid': '1',
        'receive_emails': '1',
        'no_emails': '1',
        'sponsorshipplus_flag': '1',
        'bb_dd_flag': '1',
        'dd_flag': '1',
        'fb_login': '1',
    }

    FIELDS_TO_SUBMIT = {k: None for k, v in CONNECT_MAPPING.iteritems() if v}

    def __init__(self, env):
        super(MobileLoginMapping, self).__init__(env)
        self.FIELDS_TO_SUBMIT.update(self.CONSTANTS)

    # override get_connect_data to compute value for field 'login_count'
    def get_connect_data(self, odoo_object, fields_to_submit=None):
        mapped = super(MobileLoginMapping, self).get_connect_data(
            odoo_object, fields_to_submit)
        mapped['login_count'] = len(odoo_object.log_ids)
        # The mobile app expects all string values
        for key, value in mapped.iteritems():
            mapped[key] = unicode(value)
        return mapped
