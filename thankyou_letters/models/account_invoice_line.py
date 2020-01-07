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

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


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

        communication_configs = invoice_lines.mapped(
            'product_id.partner_communication_config')
        if len(communication_configs) == 1:
            communication_config = communication_configs[0]
        else:
            _logger.warning(
                "%s thank you config found, falling back to the default",
                len(communication_configs))
            communication_config = invoice_lines.get_default_thankyou_config()

        partner = self.mapped('partner_id')
        partner.ensure_one()

        existing_comm = self.env['partner.communication.job'].search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ('call', 'pending')),
            ('config_id', '=', communication_config.id),
        ] + self.env.context.get('same_job_search', []))
        if existing_comm:
            invoice_lines = existing_comm.get_objects() | invoice_lines

        thankyou_config = self.env['thankyou.config'].search(
            []).for_donation(invoice_lines)
        send_mode, auto_mode = thankyou_config.build_inform_mode(
            partner, communication_config.print_if_not_email)

        comm_vals = {
            'partner_id': partner.id,
            'config_id': communication_config.id,
            'object_ids': invoice_lines.ids,
            'need_call': thankyou_config.need_call or
            communication_config.need_call,
            'print_subject': False,
            'user_id': self.env.context.get('default_user_id') or
            thankyou_config.user_id.id,
            'send_mode': send_mode,
            'auto_send': auto_mode,
        }
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
    def get_default_thankyou_config(self):
        """
        Returns the default communication configuration regardless of
        the donation amount.
        :return: partner.communication.config record
        """
        return self.env.ref('thankyou_letters.config_thankyou_standard')
