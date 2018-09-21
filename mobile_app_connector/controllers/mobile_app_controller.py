# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Nicolas Bornand <n.badoux@hotmail.com>
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http
from odoo.http import request
from werkzeug.exceptions import NotFound, MethodNotAllowed


class RestController(http.Controller):

    # TODO : For now the route is public but we will have to see
    # how the authentication is made from the mobile app to provide
    # with a login path and only allow connected users to call this API
    @http.route('/mobile-app-api/<string:model>/<string:method>', type='json',
                auth='oauth2', methods=['GET', 'POST'])
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

    @http.route('/mobile-app-api/get-message/', type='json',
                auth='public', methods=['GET'])
    def get_message(self, **parameters):
        odoo_obj = request.env.get('res.partner')
        if odoo_obj is None or not hasattr(odoo_obj, 'mobile_get_message'):
            raise NotFound("Unknown API path called.")

        handler = getattr(odoo_obj.sudo(), 'mobile_get_message')
        return handler(**parameters)

    @http.route('/mobile-app-api/correspondence/letter_pdf',
                type='http', auth='public', methods=['GET'])
    def download_pdf(self, **parameters):
        pdf = request.env['compassion.child'].sudo() \
            .mobile_letter_pdf(**parameters)
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf))
        ]
        return request.make_response(pdf, headers=headers)
