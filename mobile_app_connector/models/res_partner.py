# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models


class GetPartnerMessage(models.Model):
    _inherit = "res.partner"

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    @api.model
    def mobile_get_all_correspondence(self, **other_params):
        values = dict(other_params)
        partner = self.env['res.partner'].search([
            ('id', '=', values['partner_id'])
        ])
        child = self.env['compassion.child'].search([
            ('global_id', '=', str(values['child_global_id']))
        ])
        correspondences = self.env['correspondence'].search([
            ('partner_id', '=', partner.id),
            ('child_id', '=', child.id)
        ])

        result = []
        for corres in correspondences:
            text = corres.english_text or corres.original_text
            # check who is sending the letter (admitting that sender signs
            # at the end)
            partner_sending = text.endswith((partner.name,
                                             partner.name.split(" ")[0],
                                             partner.name.split(" ")[1]))
            result.append({
                "CancelCard": None,
                "CancelLetter": None,
                "CardFrom": None,
                "CardMessage": None,
                "CardTo": None,
                "LetterFrom": partner.name if partner_sending else child.name,
                "LetterMessage": text,  # or maybe english_text
                "LetterTo": child.name if partner_sending else partner.name,
                "ReceivedDate": corres.scanned_date  # surely wrong date
            })
        return result
