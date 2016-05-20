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

from openerp import fields, models


class SponsorshipGift(models.Model):
    _name = 'sponsorship.gift'

    # Related records
    #################
    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True
    )
    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship'
    )
    project_id = fields.Many2one(
        'compassion.project', 'Project'
    )
    child_id = fields.Many2one(
        'compassion.child', 'Child'
    )
    invoice_line_ids = fields.Many2many(
        'account.invoice.line', 'Invoice lines'
    )
    payment_id = fields.Many2one(
        'account.move', 'Payment'
    )

    # Gift information
    ##################
    gmc_gift_id = fields.Char()
    date_partner_paid = fields.Date()
    date_sent = fields.Datetime()
    date_money_sent = fields.Datetime()
    amount = fields.Float()
    instructions = fields.Char()
    gift_type = fields.Selection([
        ('Project Gift', 'Project Gift'),
        ('Family Gift', 'Family Gift'),
        ('Beneficiary Gift', 'Beneficiary Gift'),
    ])
    attribution = fields.Selection([
        ('Center Based Programming', 'CDSP'),
        ('Home Based Programming (Survival & Early Childhood)', 'CSP'),
        ('Survival Neediest Families', 'Neediest Families'),
        ('Sponsored Child Family', 'Sponsored Child Family'),
        ('Survival Neediest', 'Survival Neediest'),
        ('Sponsorship', 'Sponsorship'),
    ])
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
    ])
    gmc_state = fields.Selection([
        ('draft', 'Not in the system'),
        ('In Progress (Active)', 'In Progress'),
        ('Delivered', 'Delivered'),
        ('Undeliverable', 'Undeliverable'),
    ])
    undeliverable_reason = fields.Selection([
        ('Project Transitioned', 'Project Transitioned'),
        ('Beneficiary Exited', 'Beneficiary Exited'),
        ('Beneficiary Exited More Than 90 Days Ago',
         'Beneficiary Exited More Than 90 Days Ago'),
    ])
    threshold_alert = fields.Boolean(
        help='Partner exceeded the maximum gift amount allowed')
