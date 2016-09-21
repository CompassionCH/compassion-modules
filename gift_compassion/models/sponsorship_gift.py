# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import fields, models, api


class SponsorshipGift(models.Model):
    _name = 'sponsorship.gift'

    # Related records
    #################
    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship', required=True
    )
    partner_id = fields.Many2one(
        'res.partner', 'Partner', related='sponsorship_id.partner_id',
        store=True
    )
    project_id = fields.Many2one(
        'compassion.project', 'Project',
        related='sponsorship_id.child_id.project_id', store=True
    )
    child_id = fields.Many2one(
        'compassion.child', 'Child', related='sponsorship_id.child_id',
        store=True
    )
    invoice_line_ids = fields.Many2many(
        'account.invoice.line', string='Invoice lines', required=True,
    )
    payment_id = fields.Many2one(
        'account.move', 'Payment'
    )

    # Gift information
    ##################
    name = fields.Char(compute='_compute_name')
    gmc_gift_id = fields.Char()
    date_partner_paid = fields.Date(
        compute='_compute_invoice_fields', store=True
    )
    date_sent = fields.Datetime()
    date_money_sent = fields.Datetime()
    amount = fields.Float(compute='_compute_invoice_fields', store=True)
    instructions = fields.Char()
    gift_type = fields.Selection([
        ('Project Gift', 'Project Gift'),
        ('Family Gift', 'Family Gift'),
        ('Beneficiary Gift', 'Beneficiary Gift'),
    ], required=True)
    attribution = fields.Selection([
        ('Center Based Programming', 'CDSP'),
        ('Home Based Programming (Survival & Early Childhood)', 'CSP'),
        ('Survival Neediest Families', 'Neediest Families'),
        ('Sponsored Child Family', 'Sponsored Child Family'),
        ('Survival Neediest', 'Survival Neediest'),
        ('Sponsorship', 'Sponsorship'),
    ], required=True)
    sponsorship_gift_type = fields.Selection([
        ('Birthday', 'Birthday'),
        ('General', 'General'),
        ('Graduation/Final', 'Graduation/Final'),
    ])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Verify'),
        ('open', 'Pending'),
        ('fund_due', 'Fund Due'),
        ('fund_delivered', 'Fund Delivered'),
    ], default='draft')
    gmc_state = fields.Selection([
        ('draft', 'Not in the system'),
        ('In Progress (Active)', 'In Progress'),
        ('Delivered', 'Delivered'),
        ('Undeliverable', 'Undeliverable'),
    ], default='draft')
    undeliverable_reason = fields.Selection([
        ('Project Transitioned', 'Project Transitioned'),
        ('Beneficiary Exited', 'Beneficiary Exited'),
        ('Beneficiary Exited More Than 90 Days Ago',
         'Beneficiary Exited More Than 90 Days Ago'),
    ])
    threshold_alert = fields.Boolean(
        help='Partner exceeded the maximum gift amount allowed')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends('invoice_line_ids')
    def _compute_invoice_fields(self):
        for gift in self:
            pay_dates = gift.mapped('invoice_line_ids.last_payment')
            amounts = gift.mapped('invoice_line_ids.price_subtotal')
            gift.date_partner_paid = fields.Date.to_string(max(
                map(lambda d: fields.Date.from_string(d), pay_dates)))
            gift.amount = sum(amounts)

    def _compute_name(self):
        for gift in self:
            if gift.gift_type != 'Beneficiary Gift':
                name = gift.gift_type
            else:
                name = gift.sponsorship_gift_type + ' Gift'
            name += ' [' + gift.sponsorship_id.name + ']'
            gift.name = name
