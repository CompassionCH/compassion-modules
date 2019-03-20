# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import requests

from odoo import exceptions
from odoo.tools import config


class Session(requests.Session):
    def __enter__(self):
        """Authenticate and set the JSON Web Token for the session"""
        wp_host = config.get('wordpress_host')
        wp_user = config.get('wordpress_user')
        wp_pwd = config.get('wordpress_pwd')

        wp_api_url = 'https://' + wp_host + '/wp-json/jwt-auth/v1/token'

        auth = self.post(wp_api_url, json={
            'username': wp_user,
            'password': wp_pwd,
        }).json()

        if 'token' not in auth:
            raise exceptions.AccessError('Wordpress authentication failed !')

        self.headers.update({'Authorization': 'Bearer %s' % auth['token']})

        return super(Session, self).__enter__()
