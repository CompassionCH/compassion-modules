# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields
from ..mappings.compassion_invoice_mapping import \
    MobileInvoiceMapping
from datetime import date


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
        wrapper = MobileappWrapper(json_data)
        invoice_line = self.env['account.invoice.line']
        invoices_lines = invoice_line

        for i in range(0, len(wrapper.appealId)):
            product = self.env['product.template'].search(
                [('id', '=', wrapper.appealId[i])]
            )
            invoices_lines += invoice_line.create({
                'product_id': wrapper.appealId[i],
                'account_id':  product.property_account_income_id.id,
                'quantity': 1,
                'price_unit': wrapper.appealprice[i],
                'name': product.name
            })
        for i in range(0, len(wrapper.giftId)):
            product = self.env['product.template'].search(
                [('id', '=', wrapper.giftId[i])]
            ).sudo()
            child = self.env['compassion.child'].search(
                [('name', '=', wrapper.childs[i])]
            )
            sponsorship = self.env['recurring.contract'].search(
                [('child_id', '=', child.id)]
            )
            invoices_lines += invoice_line.create({
                'product_id': wrapper.giftId[i],
                'account_id':  product.property_account_income_id.id,
                'quantity': 1,
                'price_unit': wrapper.giftamount[i],
                'contract_id': sponsorship.id,
                'name': product.name
            })
            #Todo Remove the sudo after the Login function is done
        invoice = self.sudo().create({
            'partner_id': int(wrapper.partner_id),
            'invoice_line_ids': [(6, 0, invoices_lines.ids)],
            'date_due': wrapper.dateOut,
            'write_date': wrapper.dateIn})

        if invoice:
            return "The appeals/gifts have been correctly send"
        else:
            return "Cannot send the appeals/gifts"


class MobileappWrapper:

    def __init__(self, json):
        self.appealId = json['appealtype']
        self.giftId = json['gifttype']
        self.appealprice = json['appealamount']
        self.giftamount = json['giftamount']
        self.dateIn = date(json['startyear'], json['startmonth'], 1)
        self.dateOut = date(json['endyear'], json['endmonth'], 1)
        self.childs = json['childname']
        self.partner_id = json['supporter']
