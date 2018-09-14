# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, api
from ..mappings.compassion_login_mapping import MobileLoginMapping

logger = logging.getLogger(__name__)


class CompassionLogin(models.Model):
    _inherit = 'res.users'

    @api.model
    def mobile_login(self, **other_params):
        """
        Mobile app method:
        Log a given user.
        :param view: login view
        :param username: the username of the user
        :param password: the password of the user
        :param other_params: all request parameters
        :return: JSON filled with user's info
        """
        username = self._get_required_param('username', other_params)
        password = self._get_required_param('password', other_params)

        user = self.search([
            ('login', '=', username)
        ], limit=1)
        if user:
            user.sudo(user.id).check_credentials(password)

        mapping = MobileLoginMapping(self.env)
        result = mapping.get_connect_data(user)
        return result

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError('Required parameter {}'.format(key))
        return params[key]
