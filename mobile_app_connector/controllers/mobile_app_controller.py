# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http, _
from odoo.http import request
from werkzeug.exceptions import NotFound, MethodNotAllowed


class RestController(http.Controller):

    # TODO : For now the route is public but we will have to see
    # how the authentication is made from the mobile app to provide
    # with a login path and only allow connected users to call this API
    @http.route('/mobile-app-api/<string:model>/<string:method>', type='json',
                auth='public', methods=['GET', 'POST'])
    def mobile_app_handler(self, model, method, **parameters):
        odoo_obj = request.env.get(model)
        model_method = 'mobile_' + method
        if odoo_obj is None or not hasattr(odoo_obj, model_method):
            raise NotFound("Unknown API path called.")

        handler = getattr(odoo_obj.sudo(), model_method)
        if request.httprequest.method == 'GET':
            return handler(**parameters)
        elif request.httprequest.method == 'POST':
            return handler(request.jsonrequest, **parameters)
        else:
            raise MethodNotAllowed("Only POST and GET methods are supported")
