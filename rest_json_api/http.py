import json
import re

from werkzeug.exceptions import BadRequest

from odoo.http import JsonRequest
from odoo.tools import date_utils


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

    def _json_response(self, result=None, error=None):
        if isinstance(error, dict) and error.get("code") == 200:
            error_message = error.get("data", {}).get("message", "")
            if error_message:
                error_code = re.search(
                    r"^\d{3}", error_message
                ).group()  # match 3 digits (int)
                if error_code:
                    error["code"] = int(error_code)
                    error["http_status"] = int(error_code)
                error["message"] = error.get("message", "") + " " + error_message
        odoo_result = super()._json_response(result, error)
        if result is not None and error is None:
            odoo_result.data = json.dumps(result, default=date_utils.json_default)
        return odoo_result
