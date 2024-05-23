import json
import logging
import re

from werkzeug.exceptions import BadRequest

from odoo.http import JsonRequest
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)


class RestJSONRequest(JsonRequest):
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
        except BadRequest as error:
            # Put simply an empty JSON data
            if "Invalid JSON data" in error.description:
                self.jsonrequest = {}
                # PUT The GET parameters as the parameters for the controller
                self.params = {key: val for key, val in self.httprequest.values.items()}
                self.context = dict(self.session.context)
            else:
                raise

    def dispatch(self):
        """Log the received message before processing it."""
        _logger.debug(
            "[%s] %s %s %s",
            self.httprequest.environ["REQUEST_METHOD"],
            self.httprequest.url,
            [(k, v) for k, v in self.httprequest.headers.items()],
            self.jsonrequest,
        )
        return super().dispatch()

    def _json_response(self, result=None, error=None):
        if isinstance(error, dict) and error.get("code") == 200:
            error_message = error.get("data", {}).get("message", "")
            if error_message:
                error_code = re.search(r"^\d{3}", error_message)  # match 3 digits (int)
                if error_code:
                    error["code"] = int(error_code.group())
                    error["http_status"] = int(error_code.group())
                error["message"] = error.get("message", "") + " " + error_message
        odoo_result = super()._json_response(result, error)
        if result is not None and error is None:
            odoo_result.data = json.dumps(result, default=date_utils.json_default)
        request_path = self.httprequest.environ["PATH_INFO"]
        self._postprocess(request_path, odoo_result)
        _logger.debug(
            '[SEND] %s %s "%s"', odoo_result.status, odoo_result.headers, result
        )
        return odoo_result

    def _handle_exception(self, exception):
        request_path = self.httprequest.environ["PATH_INFO"]
        custom_response = self._custom_exception(exception, request_path)
        if custom_response:
            return custom_response
        return super()._handle_exception(exception)

    def _postprocess(self, request_path, odoo_result):
        # Hook for custom post-processing
        pass

    def _custom_exception(self, exception, request_path):
        # Hook for custom exception handling
        pass
