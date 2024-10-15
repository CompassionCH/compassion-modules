import collections.abc
import logging
from datetime import datetime

import werkzeug

from odoo import exceptions
from odoo.http import (
    SessionExpiredException,
)
from odoo.tools import config

from odoo.addons.rest_json_api.http import RestJsonDispatcher

_logger = logging.getLogger(__name__)

TEST_MODE = config.get("test_enable")


class OnrampJsonDispatcher(RestJsonDispatcher):
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

    routing_type = "onramp"

    def _get_json_headers(self):
        # Hook for custom headers on JSON response
        return [("x-cim-RequestId", self.request_id)]

    def handle_error(self, exception: Exception) -> collections.abc.Callable:
        """
        Handle any exception that occurred while dispatching a request to
        a `type='json'` route. Also handle exceptions that occurred when
        no route matched the request path, that no fallback page could
        be delivered and that the request ``Content-Type`` was json.

        :param exception: the exception that occurred.
        :returns: a WSGI application
        """
        # Format the errors to conform to GMC error types
        error = {
            "ErrorId": self.request_id,
            "ErrorTimestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
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
                    "ErrorMessage": str(exception),
                }
            )
            if not TEST_MODE:
                _logger.error(str(exception), exc_info=True)
        elif isinstance(exception, exceptions.AccessDenied):
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

        return self._response(error=error)