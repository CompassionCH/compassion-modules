# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models
from odoo.tools.config import config
from werkzeug.exceptions import Unauthorized

_logger = logging.getLogger(__name__)


class IrHTTP(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_oauth2_app(self):
        client_id = self._oauth_validation()
        # For mobile app, we check that the token was requested from us,
        # using the GMC connect client
        authorized_client = config.get('connect_client')
        if client_id != authorized_client:
            raise Unauthorized()
