# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import werkzeug
import logging
import simplejson

from odoo.http import JsonRequest, Root
# Monkeypatch type of request root to use MobileAppJsonRequest
from odoo.addons.message_center_compassion.controllers.json_request import \
    get_request as old_get_request

_logger = logging.getLogger(__name__)


def get_request(self, httprequest):
    if (httprequest.mimetype == "application/json" and
            httprequest.environ['PATH_INFO'].startswith('/mobile-app-api')):
        return MobileAppJsonRequest(httprequest)
    return old_get_request(self, httprequest)


Root.get_request = get_request


class MobileAppJsonRequest(JsonRequest):
    """ Special RestJson Handler to accept empty JSON GET messages for
    mobile-app-api and send back results in clean JSON format
    (remove wrapper made by Odoo)
    """
    def __init__(self, *args):
        try:
            super(MobileAppJsonRequest, self).__init__(*args)
            self.params = {
                key: val for key, val in self.httprequest.args.iteritems()
            }
        except werkzeug.exceptions.BadRequest as error:
            # Put simply an empty JSON data
            if 'Invalid JSON data' in error.description:
                self.jsonrequest = {}
                # PUT The GET parameters as the parameters for the controller
                self.params = {
                    key: val for key, val in self.httprequest.args.iteritems()
                }
                self.context = dict(self.session.context)
            else:
                raise error

    def _json_response(self, result=None, error=None):
        odoo_result = super(MobileAppJsonRequest, self)._json_response(
            result, error)
        if result is not None and error is None:
            odoo_result.data = simplejson.dumps(result)
        return odoo_result
