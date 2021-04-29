##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Yannick Vaucher, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import json
import logging

from odoo import http, exceptions
from odoo.exceptions import ValidationError
from odoo.http import request
from ..tools.onramp_connector import OnrampConnector

_logger = logging.getLogger(__name__)


# Put any authorized sender here. Its address must be part of the headers
# in order to handle a request.
AUTHORIZED_SENDERS = [
    "CHTest",
    "CISalesforce",
    "CISFDC",
    "CINetsuite",
    "SFDC-CI",
    "SFCI",
    "SponsorshipPool",
]

_logger = logging.getLogger(__name__)


class RestController(http.Controller):

    @http.route("/onramp", type="json", auth="oauth2", methods=["POST"], csrf=False)
    def handler_onramp(self):
        headers = request.httprequest.headers
        message_type = headers["x-cim-MessageType"]
        OnrampConnector.log_message(
            "INCOMING", message_type, headers, request.jsonrequest
        )
        self._validate_headers(headers)
        result = {
            "ConfirmationId": request.uuid,
            "Timestamp": request.timestamp,
            "code": 200,
        }
        action_connect = (
            request.env["gmc.action.connect"]
            .sudo(request.uid)
            .search([("connect_schema", "=", message_type)])
        )
        if not action_connect:
            try:
                action_connect = (
                    request.env["gmc.action.connect"]
                    .sudo(request.uid)
                    .create({"connect_schema": message_type})
                )
            except ValidationError:
                action_connect = (
                    request.env["gmc.action.connect"]
                    .sudo(request.uid)
                    .search([("connect_schema", "=", message_type)])
                )

        action = action_connect.action_id
        params = {
            "request_id": request.uuid,
            "headers": json.dumps(dict(headers.items())),
            "content": json.dumps(request.jsonrequest, indent=4, sort_keys=True),
            "state": "success" if action_connect.ignored else "new",
        }

        if action.id:
            params["action_id"] = action.id
            result["Message"] = "Your message was successfully received."
        else:
            params["direction"] = "in"
            if action_connect.ignored:
                _logger.warning("Ignored message type received: " + message_type)
                result["Message"] = "Ignored message type - not processed."
            else:
                _logger.warning("Unknown message type received: " + message_type)
                result["Message"] = "Unknown message type - not processed."

        request.env["gmc.message"].sudo(request.uid).create(params)

        return result

    def _validate_headers(self, headers):
        from_address = headers.get("x-cim-FromAddress") or headers.get(
            "X-Cim-Fromaddress"
        )
        if from_address not in AUTHORIZED_SENDERS:
            raise exceptions.AccessDenied()
        company_obj = request.env["res.company"].sudo(request.uid)
        companies = company_obj.search([])
        country_codes = companies.mapped("partner_id.country_id.code")
        to_address = headers.get("x-cim-ToAddress") or headers.get("X-Cim-ToAddress")
        if to_address not in country_codes:
            raise AttributeError("This message is not for me.")
