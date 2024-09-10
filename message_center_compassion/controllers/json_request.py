##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Yannick Vaucher, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import uuid
from datetime import datetime

import werkzeug

from odoo import exceptions
from odoo.http import (
    AuthenticationError,
    SessionExpiredException,
)
from odoo.tools import config

from odoo.addons.rest_json_api.http import JsonRequest

_logger = logging.getLogger(__name__)

TEST_MODE = config.get("test_enable")


class RESTJsonRequest(JsonRequest):
    """Special RestJson Handler to enable custom formatted answers to
    Compassion Connect calls and error handling.

    Sample Succesful Response
    =========================
    {
        "ConfirmationId": "e0f05e27-97af-47d0-b162-5e935052aab7",
        "Timestamp": "2015-10-07T23:03:51.626Z",
        "Message": "Your message was successfully received."
    }

    Sample Unsuccessful Response
    ============================
    {
        "ErrorId":"156b633d-2fe7-48ca-94e8-fbe0b8cd560a",
        "ErrorTimestamp":"2015-10-07T23:04:40.876Z",
        "ErrorClass":"BusinessException",
        "ErrorCategory":"InputValidationError",
        "ErrorCode":"ESB4000",
        "ErrorMessage":"Request Invalid: Request contains invalid json.",
        "ErrorRetryable":false,
        "ErrorModule":"REST OnRamp",
        "ErrorSubModule":"Rest OnRamp Request Checking",
        "ErrorMethod":"RequestIsValidJson",
        "ErrorLoggedInUser":"",
        "RelatedRecordId":""
    }"""

    def __init__(self, *args):
        """Setup a GUID for any message and keep track of timestamp."""
        self.uuid = str(uuid.uuid4())
        self.timestamp = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
        try:
            super().__init__(*args)
        except Exception:
            # We pass the error at this step to avoid sending back HTML result
            # the error will be catched later by JsonRequest and return a
            # json content error message
            self.params = dict()
            self.context = dict(self.session.context)

    def _postprocess(self, request_path, odoo_result):
        """Add required headers."""
        if request_path.startswith("/onramp"):
            odoo_result.headers.append(("x-cim-RequestId", self.uuid))

    def _custom_exception(self, exception, request_path):
        if not request_path.startswith("/onramp"):
            return False
        # Format the errors to conform to GMC error types
        error = {
            "ErrorId": self.uuid,
            "ErrorTimestamp": self.timestamp,
            "ErrorClass": "BusinessException",
            "ErrorRetryable": False,
            "ErrorModule": "REST OnRamp",
            "ErrorSubModule": "Rest OnRamp Authorization",
            "ErrorMethod": "ValidateToken",
            "ErrorLoggedInUser": "",
            "RelatedRecordId": "",
        }
        if isinstance(exception, werkzeug.exceptions.HTTPException):
            # General exception, send back the exception message
            error.update(
                {
                    "ErrorCode": exception.code,
                    "ErrorCategory": "CommunicationError",
                    "ErrorMessage": exception.description,
                }
            )
            if not TEST_MODE:
                _logger.error(exception.description, exc_info=True)
        elif isinstance(exception, exceptions.AccessDenied):
            # Access error
            error.update(
                {
                    "ErrorCode": 401,
                    "ErrorCategory": "AuthorizationError",
                    "ErrorMessage": "401 Unauthorized",
                }
            )
            if not TEST_MODE:
                _logger.error("401 Unauthorized", exc_info=True)
        elif isinstance(exception, AttributeError):
            # Raised if JSON could not be parsed or invalid body was received
            error.update(
                {
                    "ErrorCode": 400,
                    "ErrorSubModule": "Rest OnRamp Message Validation",
                    "ErrorMethod": "Message Validation",
                    "ErrorCategory": "InputValidationError",
                    "ErrorMessage": exception.message,
                }
            )
            if not TEST_MODE:
                _logger.error(exception.message, exc_info=True)
        elif isinstance(exception, AuthenticationError):
            error.update(
                {
                    "ErrorCode": 401,
                    "ErrorCategory": "AuthenticationError",
                    "ErrorMessage": "Session Invalid",
                }
            )
            if not TEST_MODE:
                _logger.error("Session Invalid", exc_info=True)
        elif isinstance(exception, SessionExpiredException):
            error.update(
                {
                    "ErrorCode": 401,
                    "ErrorCategory": "AuthenticationError",
                    "ErrorMessage": "Session Expired",
                }
            )
            if not TEST_MODE:
                _logger.error("Session Expired", exc_info=True)
        else:
            # Any other cases, lookup what exception type was raised.
            if not isinstance(exception, (exceptions.UserError)):
                if not TEST_MODE:
                    _logger.error(
                        "Exception during JSON request handling.", exc_info=True
                    )
            error.update(
                {
                    "ErrorCode": 500,
                    "ErrorCategory": "ApplicationError",
                    "ErrorMessage": "Odoo Server Error",
                }
            )
        return self._json_response(error=error)
