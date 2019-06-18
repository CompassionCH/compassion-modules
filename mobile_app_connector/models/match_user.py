# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Sylvain Laydernier <sly.laydernier@yahoo.fr>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models
from odoo.addons.base.ir.ir_mail_server import MailDeliveryException


class MatchUser(models.AbstractModel):
    """
    Allows the matching of an user from some given information.
    Can be extended or inherited to change the behaviour for some particular
    case.
    """
    _name = 'res.user.match'

    @api.model
    def match_user_to_email(self, email=None):
        """
        Find the user that match the given email address (unique key)
        :param email: email used by user to login
        :return: The matched user, false if no user matches.
        """
        user_obj = self.env['res.users'].sudo()
        user = False

        if email:
            user = user_obj.search([('login', '=', email)])

        return user

    @api.model
    def reset_password(self, user, options=None):
        """

        :param user: user we want to reset password, false if matching failed
        :param options: An optional dict containing the options parameters.
        :return: Dict containing response status (0 if success, 1 if failure)
        and response message
        """
        if options is None:
            options = {}

        # Default options
        opt = {
            'skip_password_reset': False  # When True, do not reset user's
                                          # password
        }
        opt.update(options)

        # set default response
        response = {
            'status': 1,
            'message': "No such account"
        }

        # if search didn't match any user, do not reset password and return
        # default response
        if user:
            if not opt['skip_password_reset']:
                try:
                    user.action_reset_password()
                    response['status'] = 0
                    response['message'] = "Success"
                except MailDeliveryException:
                    response['message'] = "Mail delivery error"
            else:
                response['message'] = "Skipped reset"
        return response
