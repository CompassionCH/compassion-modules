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

from ..mappings.compassion_login_mapping import MobileLoginMapping
from ..mappings.app_banner_mapping import AppBannerMapping
from odoo import http
from odoo.http import request
from werkzeug.exceptions import NotFound, MethodNotAllowed, Unauthorized


class RestController(http.Controller):

    @http.route('/mobile-app-api/login', type='json', methods=['GET'],
                auth='public')
    def mobile_app_login(self, username, password, **kwargs):
        """
        This is the first entry point for logging, which will setup the
        session for the user so that he can later call the main entry point.

        :param username: odoo user login
        :param password: odoo user password
        :param view: mobile app view from which the request was made
        :return: json user data
        """
        request.session.authenticate(
            request.session.db, username, password)
        mapping = MobileLoginMapping(request.env)
        return mapping.get_connect_data(request.env.user)

    @http.route(['/mobile-app-api/<string:model>/<string:method>',
                 '/mobile-app-api/<string:model>/<string:method>/'
                 '<request_code>'],
                type='json', auth='user', methods=['GET', 'POST'])
    def mobile_app_handler(self, model, method, **parameters):
        """
        Main entry point for all authenticated calls (user is logged in).
        :param model: odoo model object in which we are requesting something
        :param method: method that will be called on the odoo model
        :param parameters: all other optional parameters sent by the request
        :return: json data for mobile app
        """
        odoo_obj = request.env.get(model)
        model_method = 'mobile_' + method
        if odoo_obj is None or not hasattr(odoo_obj, model_method):
            raise NotFound("Unknown API path called.")

        handler = getattr(odoo_obj, model_method)
        if request.httprequest.method == 'GET':
            return handler(**parameters)
        elif request.httprequest.method == 'POST':
            return handler(request.jsonrequest, **parameters)
        else:
            raise MethodNotAllowed("Only POST and GET methods are supported")

    @http.route('/mobile-app-api/hub/<int:partner_id>', type='json',
                auth='public', methods=['GET'])
    def get_hub_messages(self, partner_id, **parameters):
        """
        This route is not authenticated with user, because it can be called
        without login.
        :param partner_id: 0 for public, or partner id.
        :return: messages for displaying the hub
        """
        hub_obj = request.env['mobile.app.hub'].sudo()
        if partner_id:
            # Check if requested url correspond to the current user
            if partner_id == request.env.user.partner_id.id:
                # This will ensure the user is logged in
                request.session.check_security()
                hub_obj = hub_obj.sudo(request.session.uid)
            else:
                raise Unauthorized()
        return hub_obj.mobile_get_message(partner_id=partner_id, **parameters)

    @http.route('/mobile-app-api/hero/', type='json',
                auth='public', methods=['GET'])
    def get_hero(self, view=None, **parameters):
        """
        Hero view is the main header above the HUB in the app.
        We return here what should appear in this view.
        :param view: always "hero"
        :param parameters: other parameters should be empty
        :return: list of messages to display in header
                 note: only one item is used by the app.
        """
        hero = request.env['mobile.app.banner'].search([
            ('is_active', '=', True)
        ], limit=1)
        hero_mapping = AppBannerMapping(request.env)
        res = hero_mapping.get_connect_data(hero)
        return [res]

    @http.route('/mobile-app-api/donation_type/', type='json',
                auth='public', methods=['GET'])
    def get_donation_type(self, view=None, **parameters):
        """
        This is called by the App to list all donation funds available.
        TODO the FundNames are hardcoded in the app, so we cannot send
        whatever we like. We want to discuss with UK if we can change this
        and have an object in Odoo to configure the active funds we want
        to promote in the app (with product_id link and picture defined in
        Odoo)
        :param view: ??
        :param parameters: ??
        :return: Json
        """
        return request.env['product.template'].sudo().mobile_donation_type()

    @http.route('/mobile-app-api/correspondence/letter_pdf',
                type='json', auth='user', methods=['GET'])
    def download_pdf(self, **parameters):
        host = request.env['ir.config_parameter'].get_param('web.base.url')
        letter_id = parameters['correspondenceid']
        letter = request.env['correspondence'].browse([int(letter_id)])
        if letter.exists() and letter.letter_image:
            return host + "b2s_image?id=" + letter.uuid
        raise NotFound()
