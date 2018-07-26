# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class GetPartnerMessage(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_message(self, **other_params):
        values = dict(other_params)
        partner_id = values['partner']
        nb_sponsorships = len(self.env['recurring.contract'].search([
            ('partner_id', '=', partner_id.id)
        ]))

        messages = [{
            "ActionDestination": "Child selector",
            "Body": "You're changing" + str(nb_sponsorships) + "lives",
            "SortOrder": 1001,
            "SubType": "CH1",
            "Title": "Thank You",
            "Type": "Child"
        }]

        links = {
            "Base": "<base url here>",
            "Next": "/mobile-app-api/get-message/" + str(partner_id.id)
                    + "?limit=1&start=1",
            "Self": "<base url here>/mobile-app-api/get-message/" + str(
                partner_id.id) + "?limit=1&start=0"
        }

        response = {
            "Limit": 1,
            "Messages": messages,
            "Size": 1,
            "Start": 0,
            "_Links": links
        }
        return response
