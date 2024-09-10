import logging
import re

import pyquerystring

from odoo.http import JsonRPCDispatcher

_logger = logging.getLogger(__name__)


class RestJsonDispatcher(JsonRPCDispatcher):
    """
    Special RestJson Handler to accept empty JSON GET messages for
    mobile-app-api and send back results in clean JSON format
    (remove wrapper made by Odoo)
    """

    routing_type = "rest_json"

    def dispatch(self, endpoint, args):
        request = self.request.httprequest
        try:
            self.jsonrequest = self.request.get_json_data()
            self.request_id = self.jsonrequest.get("id")
            self.request.params = dict(self.jsonrequest.get("params", {}), **args)
        except (ValueError, AttributeError):
            # PUT The GET parameters as the parameters for the controller
            self.jsonrequest = {}
            self.request.params = pyquerystring.parse(
                request.query_string.decode("utf-8")
            )

        _logger.debug(
            "[%s] %s %s %s",
            request.environ["REQUEST_METHOD"],
            request.url,
            [(k, v) for k, v in request.headers.items()],
            self.jsonrequest,
        )
        if self.request.db:
            result = self.request.registry["ir.http"]._dispatch(endpoint)
        else:
            result = endpoint(**self.request.params)
        return self._response(result)

    def _response(self, result=None, error=None):
        status = 200
        if isinstance(error, dict) and error.get("code") == 200:
            error_message = error.get("data", {}).get("message", "")
            if error_message:
                # match 3 digits (int)
                error_code = re.search(r"^\d{3}", error_message)
                if error_code:
                    status = int(error_code.group())
                    error["code"] = status
                    error["http_status"] = status
                error["message"] = error.get("message", "") + " " + error_message
        if result is not None and error is None:
            response = result
        else:
            response = {
                "error": error,
            }
        headers = self._get_json_headers()
        _logger.debug('[SEND] %s %s "%s"', status, headers, result)
        return self.request.make_json_response(response, headers=headers, status=status)

    def _get_json_headers(self):
        # Hook for custom headers on JSON response
        return []
