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
import werkzeug

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

    @http.route('/mobile-app-api/firebase.registration/register',
                auth='public', method='POST', type='json')
    def firebase_registration(self, **parameters):
        """
        Handle firebase registration coming from the app when no user is logged
        in.
        :param parameters: Request params
        :return: Request results
        """
        return request.env.get('firebase.registration').mobile_register(
            request.jsonrequest, **parameters)

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
        # Increment banner's print_count value
        hero.sudo().print_count += 1
        hero_mapping = AppBannerMapping(request.env)
        res = hero_mapping.get_connect_data(hero)
        return [res]

    @http.route('/sponsor_a_child/<string:lang_code>/<string:source>',
                type='http', auth='public', website=True)
    def mobile_app_sponsorship_request(self, lang_code=None, source=None,
                                       **parameters):
        """
        Create a sms_child_request and redirect user to sms sponsorship form
        It uses sms sponsorship
        :return: Redirect to sms_sponsorship form
        """
        public_partner = request.env.ref('base.public_partner')
        partner = request.env.user.partner_id
        values = {
            'lang_code': lang_code,
            'source': source,
            'partner_id': partner.id if partner != public_partner else False,
        }
        sms_child_request = request.env['sms.child.request'].\
            sudo().create(values)
        return werkzeug.utils.redirect(sms_child_request.step1_url, 302)

    @http.route('/mobile-app-api/forgot-password',
                type='json', auth='public', methods=['GET'])
    def mobile_app_forgot_password(self, **parameters):
        """
        Called by app when user forgot his password, try to match his email
        address and then send him reset instructions
        :return:
        """
        if 'email' not in parameters:
            return {
                'status': 1,
                'message': "No email entered"
                    }
        match_obj = request.env['res.user.match']
        user = match_obj.sudo().match_user_to_email(parameters['email'])
        return match_obj.sudo().reset_password(user)
