import logging
import uuid
from datetime import datetime

from starlette.datastructures import Headers

from odoo.exceptions import ValidationError
from odoo.models import AbstractModel
from odoo.tools.json import scriptsafe as json

from ..tools.onramp_connector import OnrampConnector

_logger = logging.getLogger(__name__)


class OnrampService(AbstractModel):
    _name = "onramp.service"
    _description = "Onramp Service"

    def handle_incoming_message(self, headers: Headers, body: str):
        """
        Handle incoming messages from Onramp.
        This method should be called by the FastAPI endpoint.
        """
        message_type = headers["x-cim-MessageType"]
        OnrampConnector.log_message("INCOMING", message_type, headers, body)
        result = {
            "ConfirmationId": str(uuid.uuid4()),
            "Timestamp": datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S"),
            "code": 200,
        }
        action_connect = self.env["gmc.action.connect"].search(
            [("connect_schema", "=", message_type)]
        )
        if not action_connect:
            try:
                action_connect = self.env["gmc.action.connect"].create(
                    {"connect_schema": message_type}
                )
            except ValidationError:
                action_connect = self.env["gmc.action.connect"].search(
                    [("connect_schema", "=", message_type)]
                )

        action = action_connect.action_id
        params = {
            "request_id": result["ConfirmationId"],
            "headers": json.dumps(dict(headers.items())),
            "content": json.dumps(body, indent=4, sort_keys=True),
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

        self.env["gmc.message"].create(params)

        return result
