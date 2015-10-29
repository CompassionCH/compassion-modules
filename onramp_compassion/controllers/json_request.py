# -*- coding: utf-8 -*-
#
#    Author: Yannick Vaucher
#    Copyright 2015 Camptocamp SA
#
import simplejson
import werkzeug
import logging
import uuid
from datetime import datetime

from ..tools.onramp_logging import ONRAMP_LOGGER
from openerp import exceptions
from openerp.http import (
    Response, JsonRequest, Root, SessionExpiredException,
    AuthenticationError
)

_logger = logging.getLogger(__name__)

# Monkeypatch type of request rooter to use RESTJsonRequest
old_get_request = Root.get_request


def get_request(self, httprequest):
    if (httprequest.mimetype == "application/json"
            and httprequest.environ['PATH_INFO'].startswith('/onramp')):
        return RESTJsonRequest(httprequest)
    return old_get_request(self, httprequest)

Root.get_request = get_request


class RESTJsonRequest(JsonRequest):

    def __init__(self, *args):
        self.uuid = str(uuid.uuid4())
        self.timestamp = datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S')
        try:
            super(RESTJsonRequest, self).__init__(*args)
        except AttributeError:
            raise werkzeug.exceptions.BadRequest()

    def dispatch(self):
        ONRAMP_LOGGER.info(
            "[%s] %s %s",
            self.httprequest.environ['REQUEST_METHOD'],
            self.httprequest.url,
            self.jsonrequest,
        )
        return super(RESTJsonRequest, self).dispatch()

    def _json_response(self, result=None, error=None):
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

        http_response = Response(
            body, headers=[('Content-Type', mime),
                           ('Content-Length', len(body))], status=status)
        ONRAMP_LOGGER.info("[SEND] %s %s", str(status), response)
        return http_response

    def _handle_exception(self, exception):
        """Use http exception handler."""
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
            return super(JsonRequest, self)._handle_exception(exception)
        except werkzeug.exceptions.HTTPException:
            error.update({
                'ErrorCode': exception.code,
                'ErrorCategory': 'CommunicationError',
                'ErrorMessage': exception.message,
                'description': exception.description,
            })
            return self._json_response(error=error)
        except exceptions.AccessDenied:
            error.update({
                'ErrorCode': 401,
                'ErrorCategory': 'AuthorizationError',
                'ErrorMessage': '401 Unauthorized',
            })
            return self._json_response(error=error)
        except Exception:
            if not isinstance(exception, (exceptions.Warning,
                              SessionExpiredException)):
                _logger.exception("Exception during JSON request handling.")
            error.update({
                'ErrorCode': 500,
                'ErrorCategory': 'ApplicationError',
                'ErrorMessage': 'Odoo Server Error',
                # 'data': serialize_exception(exception)
            })
            if isinstance(exception, AuthenticationError):
                error.update({
                    'ErrorCode': 401,
                    'ErrorCategory': 'AuthenticationError',
                    'ErrorMessage': 'Session Invalid',
                })
            if isinstance(exception, SessionExpiredException):
                error.update({
                    'ErrorCode': 401,
                    'ErrorCategory': 'AuthenticationError',
                    'ErrorMessage': 'Session Expired',
                })
            return self._json_response(error=error)
