# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class ThankYouConfig(models.Model):
    _name = 'thankyou.config'
    _description = 'Thank You Configuration'
    _order = "min_donation_amount"

    min_donation_amount = fields.Integer("Minimum Donation Amount",
                                         help="Amount in the local currency to "
                                              "apply the configuration")
    send_mode = fields.Selection('get_send_modes', required=True)
    thanker_user = fields.Many2one('res.users', string='Thanker')

    @api.multi
    def for_donation_amount(self, total_amount):
        assert (len(
            self) > 0), 'There should be at least one Thank you configuration.'
        # Cover the case where the total_amount is smaller that all min_donation
        # amount.
        config = self[0]
        for thankyou_config in self:
            if total_amount >= thankyou_config.min_donation_amount:
                config = thankyou_config
        return config

    def get_send_modes(self):
        return self.env['partner.communication.config'].get_send_mode()

    def build_inform_mode(self, partner):
        """ Returns how the partner should be informed for the given
        thank you letter (digital, physical or False).
        It makes the product of the thank you preference and the partner
        :returns: send_mode (physical/digital/False), auto_mode (True/False)
        """
        return self.env['partner.communication.config'] \
            .build_inform_mode(partner, self.send_mode,
                               print_if_not_email=False,
                               send_mode_pref_field='none')
