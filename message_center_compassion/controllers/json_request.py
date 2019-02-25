# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Yannick Vaucher, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import simplejson
import werkzeug
import logging
import uuid
from datetime import datetime

from odoo import exceptions
from odoo.http import (
    Response, JsonRequest, Root, SessionExpiredException,
    AuthenticationError
)

_logger = logging.getLogger(__name__)

# Monkeypatch type of request rooter to use RESTJsonRequest
old_get_request = Root.get_request


def get_request(self, httprequest):
    if (httprequest.mimetype == "application/json" and
            httprequest.environ['PATH_INFO'].startswith('/onramp')):
        return RESTJsonRequest(httprequest)
    return old_get_request(self, httprequest)


Root.get_request = get_request


class RESTJsonRequest(JsonRequest):
    """ Special RestJson Handler to enable custom formatted answers to
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
}
"""
    def __init__(self, *args):
        """ Setup a GUID for any message and keep track of timestamp. """
        self.uuid = str(uuid.uuid4())
        self.timestamp = datetime.strftime(
            datetime.now(), '%Y-%m-%dT%H:%M:%S')
        try:
            super(RESTJsonRequest, self).__init__(*args)
        except:
            # We pass the error at this step to avoid sending back HTML result
            # the error will be catched later by JsonRequest and return a
            # json content error message
            self.params = dict()
            self.context = dict(self.session.context)

    def dispatch(self):
        """ Log the received message before processing it. """
        _logger.info(
            "[%s] %s %s %s",
            self.httprequest.environ['REQUEST_METHOD'],
            self.httprequest.url,
            [(k, v) for k, v in self.httprequest.headers.iteritems()],
            self.jsonrequest,
        )
        return super(RESTJsonRequest, self).dispatch()

    def _json_response(self, result=None, error=None):
        """ Format the answer and add required headers. """
        response = {}
        status = 200
        if error is not None:
            status = error.get('ErrorCode')
            response = error
        if result is not None:
            status = result.pop('code')
            response = result

        mime = 'application/json'
        body = simplejson.dumps(response)
        headers = [
            ('Content-Type', mime),
            ('Content-Length', len(body)),
            ('x-cim-RequestId', self.uuid),
        ]

        http_response = Response(
            body, headers=headers, status=status)
        _logger.info('[SEND] %s %s "%s"', status, headers, response)
        return http_response

    def _handle_exception(self, exception):
        """Format the errors to conform to GMC error types."""
        error = {
            'ErrorId': self.uuid,
            'ErrorTimestamp': self.timestamp,
            'ErrorClass': 'BusinessException',
            'ErrorRetryable': False,
            'ErrorModule': 'REST OnRamp',
            'ErrorSubModule': 'Rest OnRamp Authorization',
            'ErrorMethod': 'ValidateToken',
            'ErrorLoggedInUser': '',
            'RelatedRecordId': ''
        }
        try:
            super(JsonRequest, self)._handle_exception(exception)
        except werkzeug.exceptions.HTTPException:
            # General exception, send back the exception message
            error.update({
                'ErrorCode': exception.code,
                'ErrorCategory': 'CommunicationError',
                'ErrorMessage': exception.description,
            })
            _logger.error(exception.description, exc_info=True)
        except exceptions.AccessDenied:
            # Access error
            error.update({
                'ErrorCode': 401,
                'ErrorCategory': 'AuthorizationError',
                'ErrorMessage': '401 Unauthorized',
            })
            _logger.error('401 Unauthorized', exc_info=True)
        except AttributeError:
            # Raised if JSON could not be parsed or invalid body was received
            error.update({
                'ErrorCode': 400,
                'ErrorSubModule': 'Rest OnRamp Message Validation',
                'ErrorMethod': 'Message Validation',
                'ErrorCategory': 'InputValidationError',
                'ErrorMessage': exception.message,
            })
            _logger.error(exception.message, exc_info=True)
        except AuthenticationError:
                error.update({
                    'ErrorCode': 401,
                    'ErrorCategory': 'AuthenticationError',
                    'ErrorMessage': 'Session Invalid',
                })
                _logger.error('Session Invalid', exc_info=True)
        except SessionExpiredException:
                error.update({
                    'ErrorCode': 401,
                    'ErrorCategory': 'AuthenticationError',
                    'ErrorMessage': 'Session Expired',
                })
                _logger.error('Session Expired', exc_info=True)
        except Exception:
            # Any other cases, lookup what exception type was raised.
            if not isinstance(exception, (exceptions.UserError)):
                _logger.exception(
                    "Exception during JSON request handling.", exc_info=True)
            error.update({
                'ErrorCode': 500,
                'ErrorCategory': 'ApplicationError',
                'ErrorMessage': 'Odoo Server Error',
            })

        finally:
            return self._json_response(error=error)
