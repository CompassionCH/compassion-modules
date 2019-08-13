# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models
from odoo.addons.firebase_connector.controllers.firebase_controller\
    import RestController as Firebase

import logging


class GetPartnerMessage(models.Model):
    _inherit = "firebase.registration"

    receive_child_notification = fields.Boolean()
    receive_general_notification = fields.Boolean()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def mobile_update_notification_preference(self, json_data, **params):
        """
        This is called when the user updates his notification preferences.
        :param params: {
            "firebaseId": the firebase id of the device where the request
                          originated
            "appchild": boolean (receive child notification)
            "appinfo": boolean (receive general notifications)
        }
        :return:
        """
        firebase_id = json_data.get('firebaseId')
        partner_id = json_data.get('SupporterId'),
        reg = self.env['firebase.registration'].search([
            ('registration_id', '=', firebase_id)])

        if len(reg) == 0:
            # id is not yet registered in Odoo
            logging.warning("Received a notification preference for a device "
                            "not yet registered in Odoo. It should not happen "
                            "in the normal registration flow.")
            self.mobile_register(json_data, {
                'operation': 'Insert',
                'supId': partner_id,
                'firebaseId': firebase_id,
            })
        else:
            reg.receive_child_notification = json_data.get('appchild') == '1'
            reg.receive_general_notification = json_data.get('appinfo') == '1'

        return {
            "UpdateRecordingContactResult":
            "App notification Child And App notification child Info updated "
            "of Supporter ID : {} ({} {}, {})".format(
                partner_id,
                firebase_id,
                reg.receive_child_notification,
                reg.receive_general_notification,)
        }

    @api.model
    def mobile_register(self, json_data, **params):
        """
        This function redirect mobile app request to register and deregister
        Firebase ids from Odoo. It redirects to the correct function in the
        firebase_connector module.
        :param json_data: since the request is urlformencoded this field is
                          usually empty and we look for data in params
        :param params: {
                    firebaseId: the firebase token from the device
                    operation: Insert or Delete, depending if un/ registering
                    supId: optional partner_id as stored in Odoo
               }
        :return: the return value of register firebase
        """

        firebase_id = params['firebaseId']
        operation = params['operation']
        partner_id = params.get('supId', None)
        if partner_id == "":
            partner_id = None
        logging.debug(
            operation + "ing a Firebase ID from partner id: " +
            str(partner_id) + " with value: " + firebase_id)

        if operation == 'Insert':
            reg_id = Firebase().firebase_register(
                registration_id=firebase_id,
                partner_id=partner_id,
            )
        elif operation == 'Delete':
            reg_id = Firebase().firebase_unregister(
                registration_id=firebase_id,
                partner_id=partner_id
            )
        else:
            raise NotImplemented('Operation %s is not supported by Odoo' %
                                 operation)

        return reg_id
