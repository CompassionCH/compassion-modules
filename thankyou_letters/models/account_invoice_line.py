# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.multi
    def get_donations(self):
        """
        Gets a tuple for thank_you communication
        If more than one product, product_name is False
        :return: (total_donation_amount, product_name)
        """
        res_name = False
        total = sum(self.mapped('price_subtotal'))
        total_string = "{:,}".format(int(total)).replace(',', "'")

        product_names = self.mapped('product_id.thanks_name')
        if len(product_names) == 1:
            res_name = product_names[0]

        return total_string, res_name

    @api.multi
    def generate_thank_you(self):
        """
        Creates a thank you letter communication.
        Must be called only on a single partner at a time.
        """
        invoice_lines = self.filtered('product_id.requires_thankyou')
        if not invoice_lines:
            # Avoid generating thank you if no valid invoice lines are present
            return

        small = self.env.ref('thankyou_letters.config_thankyou_small')
        standard = self.env.ref('thankyou_letters.config_thankyou_standard')
        large = self.env.ref('thankyou_letters.config_thankyou_large')

        partner = self.mapped('partner_id')
        partner.ensure_one()

        existing_comm = self.env['partner.communication.job'].search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ('call', 'pending')),
            ('config_id', 'in', (small + standard + large).ids),
        ])
        if existing_comm:
            invoice_lines = existing_comm.get_objects() | invoice_lines

        config = invoice_lines.mapped('product_id.thankyou_config')\
            or invoice_lines.get_thankyou_config()
        comm_vals = {
            'partner_id': partner.id,
            'config_id': config.id,
            'object_ids': invoice_lines.ids,
            'need_call': config.need_call,
            'print_subject': False,
        }
        send_mode = config.get_inform_mode(partner)
        comm_vals['send_mode'] = send_mode[0]
        comm_vals['auto_send'] = send_mode[1]
        success_stories = invoice_lines.mapped('product_id.success_story_id')
        if success_stories:
            existing_comm = existing_comm.with_context(
                default_success_story_id=success_stories[0].id)

        if existing_comm:
            existing_comm.write(comm_vals)
            existing_comm.refresh_text()
        else:
            existing_comm = existing_comm.create(comm_vals)
        self.mapped('invoice_id').write({
            'communication_id': existing_comm.id
        })

    @api.multi
    def get_thankyou_config(self):
        """
        Get how we should thank the selected invoice lines

            - small: < 100 CHF (or put setting thankyou_letters.small)
            - standard: 100 - 999 CHF (or put setting
                                       thankyou_letters.standard)
            - large: > 1000 CHF (or put setting thankyou_letters.large)
        :return: partner.communication.config record
        """
        small = self.env.ref('thankyou_letters.config_thankyou_small')
        standard = self.env.ref('thankyou_letters.config_thankyou_standard')
        large = self.env.ref('thankyou_letters.config_thankyou_large')

        total_amount = sum(self.mapped('price_subtotal'))
        settings = self.env['ir.config_parameter']
        if total_amount < int(settings.get_param('thankyou_letters.small',
                                                 100)):
            config = small
        elif total_amount < int(settings.get_param('thankyou_letters.small',
                                                   1000)):
            config = standard
        else:
            config = large
        return config
