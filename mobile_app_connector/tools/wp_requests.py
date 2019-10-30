# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import requests

from odoo import exceptions, _


class Session(requests.Session):
    def __init__(self, wp_config):
        """
        Sets the wordpress configuration
        :param wp_config: wordpress.configuration record
        """
        self.wp_config = wp_config
        super(Session, self).__init__()

    def __enter__(self):
        """Authenticate and set the JSON Web Token for the session"""
        wp_config = self.wp_config
        wp_api_url = 'https://' + wp_config.host + '/wp-json/jwt-auth/v1/token'

        auth = self.post(wp_api_url, json={
            'username': wp_config.user,
            'password': wp_config.password,
        }).json()

        if 'token' not in auth:
            raise exceptions.AccessError(_(
                'Wordpress authentication failed !'))

        self.headers.update({'Authorization': 'Bearer %s' % auth['token']})

        return super(Session, self).__enter__()
