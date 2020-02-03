# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields, _
from datetime import timedelta
from collections import defaultdict


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def mobile_post_invoice(self, json_data, **parameters):
        """
            Mobile app method:
            POST a Donation for a children or a pool

            When the user is paying for a single sponsorship
                - Find the related invoice (created monthly)
                - Add other potential gifts and fund donation
            When the user is paying for multiple different sponsorships
                - Merge the invoice.lines in a single invoice
            When the user is paying multiple times for the same sponsorship
                - Create a new invoice and assign a staff member
                (He wants to pay for multiple months in a row but invoices for future
                months might not exist)

            Notes:
            - Non-sponsorship-related lines will be removed upon transaction
            cancellation.
            - The app sends a single product of 50.- for the sponsorships by wrongly
            merging the fund donation into the sponsorship product
            - invoice.lines

            :param json_data:
            :param parameters:
            :return: sample response
        """
        wrapper = DonationDataWrapper(json_data, self.sudo().env)
        result = {
            'Gift': [],
            'Donation': [],
            # The typo is on purpose (UK did this)
            'SendAGiftPublishResult': 'Donation data Recieved.'
            if wrapper.gift_treated else
            'Cannot send the appeals/gifts'
        }
        if wrapper.gift_treated or not wrapper.partner_id:
            return result

        # Monthly sponsorships payments

        invoice = False
        notify = False
        date_due = False

        sponsorships_lines = self.env['account.invoice.line']
        payments = wrapper.child_gifts + wrapper.fund_donations

        if wrapper.is_multiple_months_payment():
            # User is paying for multiple months in a row, but there are probably not
            # enough open invoices so we will just create a new one and notify a staff
            # member that it needs to be processed manually
            notify = True
            # Create new invoice.lines for sponsorship_payments
            payments = wrapper.sponsorships_payments + payments
        else:
            date_filter = fields.Datetime.to_string(
                fields.date.today() - timedelta(days=365 / 2))
            for payment in wrapper.sponsorships_payments:
                # find oldest, unpaid related invoice and use its existing lines

                spn = payment['contract_id']
                open_inv = spn.mapped('invoice_line_ids.invoice_id').filtered(
                    lambda v: v.state == 'open' and v.date_invoice > date_filter)
                oldest_inv = min(open_inv, key=lambda v: v.date_due)

                lines = oldest_inv.invoice_line_ids.filtered(
                    lambda x: x.contract_id.id == spn.id and
                    x.product_id.id in spn.mapped('contract_line_ids.product_id').ids
                )

                spn_total_price = sum(lines.mapped('price_unit'))
                app_product_price = float(payment['amount'])
                assert spn_total_price == app_product_price, \
                    "Product total from the app does not correspond to the contract"

                if not invoice and len(lines) == len(oldest_inv.invoice_line_ids):
                    # we can use this invoice, it has no other lines
                    invoice = oldest_inv
                    invoice.action_invoice_cancel()
                    invoice.action_invoice_draft()
                else:
                    # will be merged, remove the lines from the existing invoice
                    lines.write({'invoice_id': False})
                    sponsorships_lines += lines
                    if not date_due or date_due > oldest_inv.date_due:
                        date_due = oldest_inv.date_due

        invoice_lines_values = []
        for payment in payments:
            l_vals = {
                'product_id': payment['product_id'].id,
                'account_id': payment['product_id'].property_account_income_id.id,
                'quantity': 1,
                'price_unit': payment['amount'],
                'name': payment['product_id'].name
            }
            if 'contract_id' in payment:
                l_vals['contract_id'] = payment['contract_id'].id

            invoice_lines_values.append(l_vals)

        # create invoice and merge lines
        if not invoice:
            lines_cmd = [(0, 0, v) for v in invoice_lines_values]
            if sponsorships_lines:
                lines_cmd = [(6, 0, sponsorships_lines.ids)] + lines_cmd
                # order is important

            invoice = self.sudo().create({
                'partner_id': wrapper.partner_id,
                'invoice_line_ids': lines_cmd,
                'origin': wrapper.source,
                'type': 'out_invoice',
                'date_invoice': fields.Date.today()
            })
        elif sponsorships_lines or invoice_lines_values:
            # add or create the lines in the existing invoice

            if sponsorships_lines:
                invoice.invoice_line_ids += sponsorships_lines
            if invoice_lines_values:
                invoice.write({
                    'invoice_line_ids': [(0, 0, v) for v in invoice_lines_values]
                })

        if date_due:
            invoice.date_due = date_due
        invoice.origin = wrapper.source

        if notify:
            partner_id = self.env['staff.notification.settings'].get_param(
                'gift_notify_ids')[0]

            invoice.message_needaction = True
            invoice.user_id = \
                self.env['res.partner'].sudo().browse(partner_id).user_ids[:1]
            invoice.message_post(
                _("This invoice created from the app need to be manually processed. "
                  "It might cancel older invoices."))

        for line in invoice.invoice_line_ids:
            bckp_price = line.price_unit
            line._onchange_product_id()
            line.price_unit = bckp_price

        invoice.action_invoice_open()

        result['Donation'].append(invoice.id)
        return result


class DonationDataWrapper:

    def __init__(self, json, env):
        self.partner_id = int(json.get('supporter', 0) or 0)
        self.gift_treated = json.get('LastInsertedDonationId') or \
            json.get('LastInsertedGiftId')
        self.source = json.get('source', 'iOS')

        self.fund_donations = []
        self.sponsorships_payments = []
        self.child_gifts = []

        fund_ids = json.get('appealtype', [])
        fund_amounts = json.get('appealamount', [])
        gift_products = json.get('gifttype', [])
        gift_amounts = json.get('giftamount', [])
        child_ids = json.get('need', [])

        # Map fund donations to products
        product_obj = env['product.product'].sudo()
        for i, product_id in enumerate(fund_ids):
            product = product_obj.search(
                [('product_tmpl_id', '=', product_id)], limit=1)
            if not product:
                raise ValueError(_("The product %s was not found") % product_id)
            self.fund_donations.append({
                'product_id': product,
                'amount': fund_amounts[i],
            })

        # Map gift_products (gifts and sponsorships payments)
        for i, product_id in enumerate(gift_products):
            product = product_obj.search(
                [('product_tmpl_id', '=', product_id)], limit=1)
            if not product:
                raise ValueError(_("The product %s was not found") % product_id)

            spn = env['recurring.contract'].search([
                ('child_id', '=', child_ids[i]),
                '|', ('correspondent_id', '=', self.partner_id),
                ('partner_id', '=', self.partner_id),
                ('state', 'not in', ['terminated', 'cancelled'])
            ]).ensure_one()
            p = {
                'contract_id': spn,
                'child_id': child_ids[i],
                'product_id': product,
                'amount': gift_amounts[i],
            }
            if product.product_tmpl_id == env.ref(
                    'sponsorship_compassion.product_template_sponsorship'):
                self.sponsorships_payments.append(p)
            else:
                self.child_gifts.append(p)

    def is_multiple_months_payment(self):
        # check whether the user is trying to pay multiple times for a single contract
        d = defaultdict(list)
        for spn in self.sponsorships_payments:
            d[spn['contract_id'].id].append(spn)
        return any(len(d[x]) > 1 for x in d)
