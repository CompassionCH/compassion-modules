##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from werkzeug.exceptions import Unauthorized

from odoo import http
from odoo.http import request


def verify_and_retrieve(registration_id, partner_id=None):
    """
    Check if the partner has the right to access the desired registration.
    :param registration_id: The registration it tries to access
    :param partner_id: The partner to be assigned
    :return: The registration matching the id
    """

    if partner_id:
        # Check if requested url correspond to the current user
        if int(partner_id) == request.env.user.partner_id.id:
            # This will ensure the user is logged in
            request.session.check_security()
        else:
            raise Unauthorized()
    existing = (
        request.env["firebase.registration"]
        .sudo()
        .search([("registration_id", "=", registration_id)])
    )

    assert len(existing) < 2, "Two firebase registration with same id"
    return existing


class RestController(http.Controller):
    @http.route(
        "/firebase/register", type="http", methods=["PUT"], auth="public", csrf=False
    )
    def firebase_register(
        self, registration_id, partner_id=None, language=None, **kwargs
    ):
        existing = verify_and_retrieve(registration_id, partner_id)
        if existing:
            existing.partner_id = partner_id
        else:
            languages_map = {
                "en": "en_US",
                "fr": "fr_CH",
                "de": "de_DE",
                "it": "it_IT",
            }

            partner_lang = request.env.user.partner_id.lang if partner_id else False

            # get the communication language.
            communication_language = (
                partner_lang if partner_lang else languages_map.get(language, False)
            )

            existing = (
                request.env["firebase.registration"]
                .sudo()
                .create(
                    {
                        "registration_id": registration_id,
                        "partner_id": partner_id,
                        "language": communication_language,
                    }
                )
            )

        return str(existing.id)

    @http.route(
        "/firebase/unregister", type="http", methods=["PUT"], auth="public", csrf=False
    )
    def firebase_unregister(self, registration_id, partner_id=None, **kwargs):
        existing = verify_and_retrieve(registration_id, partner_id)

        if not existing:
            # we didn't have this firebase id registered
            pass
        elif not existing.partner_id:
            # we already have no partner assigned
            pass
        else:
            if existing.partner_id.id == partner_id:
                logging.warning(
                    "Trying to erase a firebase registration of another user. "
                    "This should never happen as the id should follow the user"
                    " logged in."
                )
            existing.partner_id = None
        return "0"
