# -*- coding: utf-8 -*-
#
#    Author: Yannick Vaucher
#    Copyright 2015 Camptocamp SA
#
import simplejson
import werkzeug
import logging

from openerp import exceptions
from openerp.http import (
    Response, JsonRequest, Root, SessionExpiredException,
    AuthenticationError, serialize_exception
)

_logger = logging.getLogger(__name__)
_onramp_logger = logging.getLogger('ONRAMP')


class RESTJsonRequest(JsonRequest):

    def dispatch(self):
        _onramp_logger.info(
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
            response['error'] = error
            status = response['error']['code']
        if result is not None:
            response = result
            status = result['code']

        mime = 'application/json'
        body = simplejson.dumps(response)

        response = Response(body, headers=[('Content-Type', mime),
                                           ('Content-Length', len(body))],
                            status=status)
        _onramp_logger.info(response.response)
        return response

    def _handle_exception(self, exception):
        """Use http exception handler."""
        try:
            return super(JsonRequest, self)._handle_exception(exception)
        except werkzeug.exceptions.HTTPException:
            error = {
                'code': exception.code,
                'message': exception.message,
                'description': exception.description,
            }
            return self._json_response(error=error)
        except exceptions.AccessDenied:
            error = {
                'code': 401,
                'message': '401 Unauthorized',
            }
            return self._json_response(error=error)
        except Exception:
            if not isinstance(exception, (exceptions.Warning,
                              SessionExpiredException)):
                _logger.exception("Exception during JSON request handling.")
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': serialize_exception(exception)
            }
            if isinstance(exception, AuthenticationError):
                error['code'] = 100
                error['message'] = "Odoo Session Invalid"
            if isinstance(exception, SessionExpiredException):
                error['code'] = 100
                error['message'] = "Odoo Session Expired"
            return self._json_response(error=error)

old_get_request = Root.get_request


# Monkeypatch type of request rooter to use RESTJsonRequest
def get_request(self, httprequest):
    if (httprequest.mimetype == "application/json"
            and httprequest.environ['PATH_INFO'].startswith('/api/')):
        return RESTJsonRequest(httprequest)
    return old_get_request(self, httprequest)

Root.get_request = get_request
