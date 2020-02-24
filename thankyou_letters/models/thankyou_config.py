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

    min_donation_amount = fields.Integer(
        "Minimum Donation Amount",
        help="Amount in the local currency to apply the configuration")
    send_mode = fields.Selection('get_send_modes', required=True)
    need_call = fields.Selection(
        'get_need_call',
        help='Indicates we should have a personal contact with the partner'
    )
    user_id = fields.Many2one('res.users', string='Thanker', readonly=False)

    @api.multi
    def for_donation(self, invoice_lines):
        """
        Returns the thankyou.config to use given the invoice lines.
        :param invoice_lines: account.invoice.line recordset
        :return: thankyou.config record
        """
        assert (len(
            self) > 0), 'There should be at least one Thank you configuration.'
        # Cover the case where the total_amount is smaller that all min_
        # donation amount.
        config = self[0]
        total_amount = sum(invoice_lines.mapped('price_subtotal'))
        for thankyou_config in self:
            if total_amount >= thankyou_config.min_donation_amount:
                config = thankyou_config
        return config

    def get_send_modes(self):
        return self.env['partner.communication.config'].get_send_mode()

    def get_need_call(self):
        return self.env['partner.communication.config'].get_need_call()

    def build_inform_mode(self, partner, print_if_not_email=False):
        """ Returns how the partner should be informed for the given
        thank you letter (digital, physical or False).
        It makes the product of the thank you preference and the partner
        :returns: send_mode (physical/digital/False), auto_mode (True/False)
        """
        return self.env['partner.communication.config'] \
            .build_inform_mode(partner, self.send_mode,
                               print_if_not_email=print_if_not_email,
                               send_mode_pref_field=None)
