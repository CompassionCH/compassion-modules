##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

import json
import werkzeug
# Monkeypatch type of request root to use MobileAppJsonRequest
from odoo.addons.message_center_compassion.controllers.json_request import (
    get_request as old_get_request,
)

from odoo.http import JsonRequest, Root, SessionExpiredException
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)


def get_request(self, httprequest):
    if httprequest.environ["PATH_INFO"].startswith("/mobile-app-api"):
        return MobileAppJsonRequest(httprequest)
    return old_get_request(self, httprequest)


Root.get_request = get_request


class MobileAppJsonRequest(JsonRequest):
    """
    Special RestJson Handler to accept empty JSON GET messages for
    mobile-app-api and send back results in clean JSON format
    (remove wrapper made by Odoo)
    """

    def __init__(self, *args):
        try:
            # The following statement seems to have no effect but it is not the
            # case. It prevents the *super* of emptying the stream containing
            # the post data. Without it, we loose access to the post data.
            # pylint: disable=pointless-statement
            args[0].values

            super().__init__(*args)
            self.params = {key: val for key, val in self.httprequest.args.items()}
        except werkzeug.exceptions.BadRequest as error:
            # Put simply an empty JSON data
            if "Invalid JSON data" in error.description:
                self.jsonrequest = {}
                # PUT The GET parameters as the parameters for the controller
                self.params = {key: val for key, val in self.httprequest.values.items()}
                self.context = dict(self.session.context)
            else:
                raise

    def _json_response(self, result=None, error=None):
        odoo_result = super()._json_response(result, error)
        if result is not None and error is None:
            odoo_result.data = json.dumps(result, default=date_utils.json_default)
        return odoo_result

    def _handle_exception(self, exception):
        if isinstance(exception, ValueError):
            code = 400
            return self._json_response(
                error={
                    "code": code,
                    "http_code": code,
                    "http_status": code,
                    "message": str(exception),
                }
            )
        if isinstance(exception, SessionExpiredException):
            # This happens if user is not logged in while calling mobile
            # app JSON endpoints.
            code = 401
            return self._json_response(
                error={
                    "code": code,
                    "http_code": code,
                    "http_status": code,
                    "message": str(exception),
                }
            )
        # RE-Raise last error, without compromising the StackTrace
        raise
