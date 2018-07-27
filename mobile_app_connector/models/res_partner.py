# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api


class GetPartnerMessage(models.Model):
    _inherit = "res.partner"

    @api.model
    def mobile_get_message(self, **other_params):
        values = dict(other_params)
        partner_id = values['partner_id']
        nb_sponsorships = len(self.env["recurring.contract"].search([
            ('partner_id.id', '=', partner_id)
        ]))

        messages = [{
            "ActionDestination": "Child selector",
            "Body": "You're changing " + str(nb_sponsorships) + " lives",
            "SortOrder": 1001,
            "SubType": "CH1",
            "Title": "Thank You",
            "Type": "Child"
        }]

        links = {
            "Base": "http://services.compassionuk.org/"
                    "AppRest/AppRestService.svc",
            "Next": "/mobile-app-api/get-message/" + str(partner_id)
                    + "?limit=1&start=1",
            "Self": "http://services.compassionuk.org/AppRest/"
                    "AppRestService.svc/mobile-app-api/get-message/"
                    + str(partner_id) + "?limit=1&start=0"
        }

        response = {
            "Limit": 1,
            "Messages": messages,
            "Size": 1,
            "Start": 0,
            "_Links": links
        }
        return response
