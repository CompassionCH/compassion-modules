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
    def mobile_login(self, view, username, password, **other_params):
        """
        Mobile app method:
        Log a given user.
        :param view: login view
        :param username: the username of the user
        :param password: the password of the user
        :param other_params: all request parameters
        :return: JSON filled with user's info
        """
        result = {}
        if username is None:
            result['error'] = "Invalid Username or Password."
            return result

        user = self.search([
            ('new_password', '=', password),
            ('login', '=', username)
        ], limit=1)

        mapping = MobileLoginMapping(self.env)
        result = mapping.get_connect_data(user[0])
        return result
