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
    @http.route(['/mobile-app-api/<string:model>/<string:method>',
                 '/mobile-app-api/<string:model>/<string:method>/'
                 '<request_code>'],
                type='json',
                auth='oauth2_app', methods=['GET', 'POST'])
    def mobile_app_handler(self, model, method, request_code=0, **parameters):
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

    @http.route('/mobile-app-api/hero/', type='json',
                auth='public', methods=['GET'])
    def get_hero(self, hero_type=None, view=None, **parameters):
        """
        Hero view is the main header above the HUB in the app.
        We return here what should appear in this view.
        :param hero_type: "Default" == user logged in,
                          "WithoutLogin" == user not logged in.
        :param view: always "hero"
        :param parameters: other parameters should be empty
        :return: list of messages to display in header
                 note: only one item is used by the app.
        """
        return [
            {
                "ID": "13",
                "HERO_TITLE": "Bible Verses About Faith To Inspire You",
                "HERO_DESCRIPTION": "Discover a daily devotion to bring you "
                "encouragement. The Bible is full of incredible truths that "
                "remind us that we can put our faith in God and trust Him.",
                "HERO_IMAGE": "http://myuatsystems.com/appcp/upload/compassion"
                              "/Bible-verses-about-faith.jpg",
                "HERO_CTA_TEXT": "testing",
                "HERO_CTA_DESTINATION": "Blog",
                "HERO_CTA_DESTINATION_TYPE": "Internal",
                "HERO_TYPE": "WithoutLogin",
                "POST_ID": "10219",
                "POST_TITLE": "50 Powerful Bible Promises To Build Your Faith",
                "POST_URL": "http://www.myuatsystems.com/compassionWP/"
                            "?post_type=blog&p=10219",
                "CREATED_ON": "2018-09-03 19:34:37",
                "UPDATED_ON": "2019-02-18 12:11:14",
                "OA_ID": "820",
                "OA_BRAND_ID": "856",
                "USER_ID": "1566",
                "CREATED_BY": "1",
                "UPDATED_BY": "1566",
                "IS_DELETED": "0"
            },
        ]

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
