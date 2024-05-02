##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Nicolas Bornand <n.badoux@hotmail.com>
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import html

import werkzeug
from werkzeug.exceptions import NotFound, MethodNotAllowed, Unauthorized

from odoo import http, _
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.http import request

from base64 import b64decode

_logger = logging.getLogger(__name__)


def _get_lang(req, params):
    """ Fetches the lang from the request parameters. """
    lang_mapping = {"fr": "fr_CH", "en": "en_US", "de": "de_DE", "it": "it_IT"}
    app_lang = params.get("language", "")[:2]
    return lang_mapping.get(app_lang, req.env.lang)


class RestController(http.Controller):
    @http.route("/mobile-app-api/login", type="json", methods=["GET", "POST"], auth="public")
    def mobile_app_login(self, username=None, password=None, **kwargs):
        """
        This is the first entry point for logging, which will setup the
        session for the user so that he can later call the main entry point.

        :param username: odoo user login
        :param password: odoo user password
        :param view: mobile app view from which the request was made
        :return: json user data
        """
        try:
            if request.httprequest.method == "POST":
                request_data = request.jsonrequest
                request.session.authenticate(request.session.db,
                                             request_data['username'],
                                             b64decode(request_data['password']))
            # TODO remove connection through GET once app update is old enough
            elif request.httprequest.method == "GET":
                request.session.authenticate(request.session.db, username, password)
            user = request.env.user
        except:
            _logger.warning("Wrong login attempt from the app for user %s", username)
            user = request.env["res.users"]
        return user.data_to_json("mobile_app_login")

    @http.route(
        "/mobile-app-api/firebase.registration/register",
        auth="public",
        method="POST",
        type="json",
    )
    def firebase_registration(self, **parameters):
        """
        Handle firebase registration coming from the app when no user is logged
        in.
        :param parameters: Request params
        :return: Request results
        """
        return request.env.get("firebase.registration").mobile_register(
            request.jsonrequest, **parameters
        )

    @http.route(
        "/mobile-app-api/contact_us", type="json", auth="public", methods=["POST"]
    )
    def mobile_app_contact_us(self, **parameters):
        """
        This route is used when the user is logged out
        :param parameters: request parameters
        :return: json dict as expected by the app
        """
        return request.env["crm.claim"].mobile_contact_us(request.jsonrequest)

    @http.route(
        "/mobile-app-api/frequently.asked.questions/get_faq",
        type="json",
        auth="public",
        methods=["GET"],
    )
    def mobile_app_get_faq(self, **parameters):
        """
        FAQ entry point for not logged in users
        :param parameters: all other optional parameters sent by the request
        :return: json data for mobile app
        """
        return request.env.get("frequently.asked.questions").mobile_get_faq(
            **parameters
        )

    @http.route(
        "/mobile-app-api/privacy.statement.agreement/get_privacy_notice",
        type="json",
        auth="public",
        methods=["GET"],
    )
    def mobile_app_get_privacy_statement(self, **parameters):
        """
        Privacy statement entry point for not logged in users
        :param parameters: all other optional parameters sent by the request
        :return: json data for mobile app
        """
        return request.env.get("privacy.statement.agreement").mobile_get_privacy_notice(
            **parameters
        )

    @http.route(
        [
            "/mobile-app-api/<string:model>/<string:method>",
            "/mobile-app-api/<string:model>/<string:method>/<request_code>",
        ],
        type="json",
        auth="user",
        methods=["GET", "POST"],
    )
    def mobile_app_handler(self, model, method, **parameters):
        """
        Main entry point for all authenticated calls (user is logged in).
        :param model: odoo model object in which we are requesting something
        :param method: method that will be called on the odoo model
        :param parameters: all other optional parameters sent by the request
        :return: json data for mobile app
        """
        for key in parameters:
            parameters[key] = html.escape(parameters[key])

        odoo_obj = request.env.get(model).with_context(
            lang=_get_lang(request, parameters)
        )
        model_method = "mobile_" + method
        if odoo_obj is None or not hasattr(odoo_obj, model_method):
            raise NotFound("Unknown API path called.")

        handler = getattr(odoo_obj, model_method)
        if request.httprequest.method == "GET":
            return handler(**parameters)
        elif request.httprequest.method == "POST":
            key = "file_upl"
            if key in request.httprequest.files and key not in parameters:
                parameters[key] = request.httprequest.files[key]
            return handler(request.jsonrequest, **parameters)
        else:
            raise MethodNotAllowed("Only POST and GET methods are supported")

    @http.route(
        ["/no_json/correspondence/get_preview"],
        auth="user",
        methods=["POST"],
        type="http",
        csrf=False,
    )
    def get_preview(self, **parameters):
        return request.env["correspondence"].mobile_get_preview(self, **parameters)

    @http.route(
        "/mobile-app-api/hub/<int:partner_id>",
        type="json",
        auth="public",
        methods=["GET"],
    )
    def get_hub_messages(self, partner_id, **parameters):
        """
        This route is not authenticated with user, because it can be called
        without login.
        :param partner_id: 0 for public, or partner id.
        :return: messages for displaying the hub
        """
        hub_obj = (
            request.env["mobile.app.hub"]
            .with_context(lang=_get_lang(request, parameters))
            .sudo()
        )
        if partner_id:
            # Check if requested url correspond to the current user
            if partner_id == request.env.user.partner_id.id:
                # This will ensure the user is logged in
                request.session.check_security()
                hub_obj = hub_obj.with_user(request.session.uid)
            else:
                raise Unauthorized()
        return hub_obj.mobile_get_message(partner_id=partner_id, **parameters)

    @http.route("/mobile-app-api/hero/", type="json", auth="public", methods=["GET"])
    def get_hero(self, view=None, **parameters):
        """
        Hero view is the main header above the HUB in the app.
        We return here what should appear in this view.
        :param view: always "hero"
        :param parameters: other parameters should be empty
        :return: list of messages to display in header
                 note: only one item is used by the app.
        """
        hero_obj = (
            request.env["mobile.app.banner"]
            .sudo()
            .with_context(lang=_get_lang(request, parameters))
        )
        hero = hero_obj.search([], limit=1)
        # Increment banner's print_count value
        hero.print_count += 1
        res = hero.data_to_json("mobile_app_banner")
        return [res]

    @http.route("/sponsor_a_child", type="http", auth="public", website=True,
                sitemap=False)
    def mobile_app_sponsorship_request(self, **parameters):
        """
        Create a sms_child_request and redirect user to sms sponsorship form
        It uses sms sponsorship
        :return: Redirect to sms_sponsorship form
        """
        if not parameters.get('source'):
            return werkzeug.exceptions.BadRequest('Missing "source" GET parameter')

        values = {
            "lang_code": _get_lang(request, parameters),
            "source": parameters.get("source"),
            "partner_id": parameters.get("partner_id"),
        }
        sms_child_request = request.env["sms.child.request"].sudo().create(values)
        return werkzeug.utils.redirect(sms_child_request.step1_url, 302)

    @http.route("/sponsor_this_child", type="http", auth="public", website=True,
                sitemap=False)
    def mobile_app_sponsorship_request_specific_child(self, **parameters):
        """
        Create a sms_child_request for a provided child id and redirect user to sms sponsorship form
        It uses sms sponsorship
        :return: Redirect to sms_sponsorship form
        """
        if not parameters.get('source'):
            return werkzeug.exceptions.BadRequest('Missing "source" GET parameter')

        if not parameters.get("child_id"):
            redirect_parameters = f"source={parameters.get('source')}"
            if parameters.get('partner_id'):
                redirect_parameters += f"&partner_id={parameters.get('partner_id')}"
            return werkzeug.utils.redirect(f"/sponsor_a_child?{redirect_parameters}", 302)

        child = request.env['compassion.child'].sudo().search([("id", "=", parameters.get('child_id'))])

        # Get number of active requests for this child. We should not offer to sponsor a sponsored child
        number_active_sms_child_requests_for_child = request.env["sms.child.request"].sudo().search_count([
            ("child_id", "=", child.id),
            '|', ('sponsorship_confirmed', '=', True),
            ('state', '=like', 'step_')  # If the request is at step1 or step2
        ])

        # Ensure child exists, is on hold and no active sms child request exists for this child
        # Not using ensure_one() to have all under the same error
        if len(child) != 1 or not child.hold_id or number_active_sms_child_requests_for_child != 0:
            return werkzeug.exceptions.Gone('Child does not exist or is no longer available. Sorry.')

        values = {
            "lang_code": _get_lang(request, parameters),
            "source": parameters.get("source"),
            "child_id": child.id,
            "partner_id": parameters.get("partner_id"),
            # child_reserved mean that a child has been affected to the request
            # not that the child is reserved for this request only
            "state": "child_reserved"
        }
        sms_child_request = request.env["sms.child.request"].sudo().create(values)
        return werkzeug.utils.redirect(sms_child_request.step1_url, 302)

    @http.route(
        "/mobile-app-api/forgot-password", type="json", auth="public", methods=["GET"]
    )
    def mobile_app_forgot_password(self, **parameters):
        """
        Called by app when user forgot his password, try to match his email
        address to an user and then send him reset instructions
        :return: json containing status (0 if success, 1 if failed) and state
        message
        """
        if "email" not in parameters:
            return {"status": 1, "message": _("No email entered")}
        user_obj = request.env["res.users"].sudo()

        # search for an user match
        user = user_obj.search([("login", "=", parameters["email"])])

        # set default response
        response = {"status": 1, "message": _("No such account")}

        # if search didn't match any user, do not reset password and return
        # default response
        if user:
            try:
                user.action_reset_password()
                response["status"] = 0
                response["message"] = _("We sent you the reset instructions.")
            except MailDeliveryException:
                response["message"] = _("Mail delivery error")

        return response
