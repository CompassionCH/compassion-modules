##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, api, _
from odoo.http import request

logger = logging.getLogger(__name__)


class CompassionLogin(models.Model):
    _name = "res.users"
    _inherit = ["res.users", "compassion.mapped.model"]

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
        username = self._get_required_param("username", other_params)
        password = self._get_required_param("password", other_params)

        uid = request.session.authenticate(request.session.db, username, password)
        if uid is not False:
            self.save_session(request.cr, uid, request.context)

        result = self.data_to_json("mobile_app_login")
        return result

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError("Required parameter {}".format(key))
        return params[key]

    @api.multi
    def data_to_json(self, mapping_name=None):
        res = super().data_to_json(mapping_name)
        if not res:
            res = {}
        if not self:
            res["error"] = _("Wrong user or password")
        else:
            res["login_count"] = len(self.log_ids)
        for key, value in list(res.items()):
            if not value:
                res[key] = None
            else:
                res[key] = str(value)
        return res
