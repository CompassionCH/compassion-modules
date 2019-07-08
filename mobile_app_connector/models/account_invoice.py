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


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def mobile_post_invoice(self, json_data, **parameters):
        """
            Mobile app method:
            POST a Donation for a children or a pool

            :param parameters: all request parameters
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
        # TODO: could this work in public mode? We should get name info...
        if not wrapper.gift_treated and wrapper.partner_id:
            invoice_lines = []
            product_obj = self.env['product.product'].sudo()
            # Fund donations
            for i, product_id in enumerate(wrapper.fund_ids):
                product = product_obj.browse(product_id)
                invoice_lines.append({
                    'product_id': product.id,
                    'account_id':  product.property_account_income_id.id,
                    'quantity': 1,
                    'price_unit': wrapper.fund_amounts[i],
                    'name': product.name
                })
            # Sponsorship Gifts
            for i, product in enumerate(wrapper.gift_products):
                sponsorship = self.env['recurring.contract'].search([
                    ('child_id', '=', wrapper.child_ids[i]),
                    '|', ('correspondent_id', '=', wrapper.partner_id),
                    ('partner_id', '=', wrapper.partner_id),
                    ('state', 'not in', ['terminated', 'cancelled'])
                ], limit=1)
                invoice_lines.append({
                    'product_id': product.id,
                    'account_id':  product.property_account_income_id.id,
                    'quantity': 1,
                    'price_unit': wrapper.gift_amounts[i],
                    'contract_id': sponsorship.id,
                    'name': product.name
                })
            invoice = self.sudo().create({
                'partner_id': wrapper.partner_id,
                'invoice_line_ids': [(0, 0, invl) for invl in invoice_lines],
                'origin': wrapper.source,
                'type': 'out_invoice',
                'date_invoice': fields.Date.today()
            })
            for line in invoice.invoice_line_ids:
                bckp_price = line.price_unit
                line._onchange_product_id()
                line.price_unit = bckp_price
            result['Donation'].append(invoice.id)
        return result


class DonationDataWrapper:

    def __init__(self, json, env):
        self.fund_ids = json.get('appealtype', [])
        self.fund_amounts = json.get('appealamount', [])
        self.gift_products = self._get_gift_products(
            json.get('gifttype', []), env)
        self.gift_amounts = json.get('giftamount', [])
        self.child_ids = json.get('need', [])
        self.partner_id = int(json.get('supporter', 0) or 0)
        self.gift_treated = json.get('LastInsertedDonationId') or \
            json.get('LastInsertedGiftId')
        self.source = json.get('source', 'iOS')

    @staticmethod
    def _get_gift_products(gift_types, env):
        """
        Maps the app fund names to our gift products
        :param gift_types: list of product template ids sent by the app
        :param env: odoo environment
        :return: Recordset of product.product
        """
        product_obj = env['product.product']
        products = product_obj
        for gift_type in gift_types:
            product = product_obj.search([
                ('product_tmpl_id', '=', gift_type)], limit=1)
            if not product:
                raise ValueError(
                    _("The product %s was not found") % gift_type)
            products += product
        return products
