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

from openerp import fields, models, api, _
from openerp.exceptions import Warning

from openerp.addons.sponsorship_compassion.models.product import \
    GIFT_NAMES, GIFT_CATEGORY
from openerp.addons.message_center_compassion.mappings import base_mapping \
     as mapping


class SponsorshipGift(models.Model):
    _name = 'sponsorship.gift'
    _inherit = 'translatable.model'
    _order = 'date_partner_paid desc,id desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
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
        'account.invoice.line', string='Invoice lines',
    )
    payment_id = fields.Many2one(
        'account.move', 'Payment'
    )
    message_id = fields.Many2one(
        'gmc.message.pool', 'GMC message'
    )

    # Gift information
    ##################
    name = fields.Char(compute='_compute_name')
    gmc_gift_id = fields.Char(readonly=True)
    date_partner_paid = fields.Date(
        compute='_compute_invoice_fields', store=True
    )
    date_sent = fields.Datetime(related='message_id.process_date')
    date_money_sent = fields.Datetime()
    amount = fields.Float(compute='_compute_invoice_fields', store=True)
    instructions = fields.Char()
    gift_type = fields.Selection([
        ('Project Gift', _('Project Gift')),
        ('Family Gift', _('Family Gift')),
        ('Beneficiary Gift', _('Beneficiary Gift')),
    ], required=True)
    attribution = fields.Selection([
        ('Center Based Programming', 'CDSP'),
        ('Home Based Programming (Survival & Early Childhood)', 'CSP'),
        ('Sponsored Child Family', _('Sponsored Child Family')),
        ('Sponsorship', _('Sponsorship')),
        ('Survival', _('Survival')),
        ('Survival Neediest Families', _('Neediest Families')),
        ('Survival Neediest Families - Split', _('Neediest Families Split')),
    ], required=True)
    sponsorship_gift_type = fields.Selection([
        ('Birthday', _('Birthday')),
        ('General', _('General')),
        ('Graduation/Final', _('Graduation/Final')),
    ])
    state = fields.Selection([
        ('draft', _('Draft')),
        ('verify', _('Verify')),
        ('open', _('Pending')),
        ('error', _('Error')),
        ('fund_due', _('Fund Due')),
        ('fund_delivered', _('Fund Delivered')),
    ], default='draft', readonly=True)
    gmc_state = fields.Selection([
        ('draft', _('Not in the system')),
        ('sent', _('Sent to GMC')),
        ('In Progress (Active)', _('In Progress')),
        ('Delivered', _('Delivered')),
        ('Undeliverable', _('Undeliverable')),
    ], default='draft', readonly=True)
    undeliverable_reason = fields.Selection([
        ('Project Transitioned', 'Project Transitioned'),
        ('Beneficiary Exited', 'Beneficiary Exited'),
        ('Beneficiary Exited More Than 90 Days Ago',
         'Beneficiary Exited More Than 90 Days Ago'),
    ], readonly=True)
    threshold_alert = fields.Boolean(
        help='Partner exceeded the maximum gift amount allowed',
        readonly=True)
    field_office_notes = fields.Char()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends('invoice_line_ids')
    def _compute_invoice_fields(self):
        for gift in self.filtered('invoice_line_ids'):
            pay_dates = gift.mapped('invoice_line_ids.last_payment')
            amounts = gift.mapped('invoice_line_ids.price_subtotal')
            gift.date_partner_paid = fields.Date.to_string(max(
                map(lambda d: fields.Date.from_string(d), pay_dates)))
            gift.amount = sum(amounts)

    def _compute_name(self):
        for gift in self:
            if gift.gift_type != 'Beneficiary Gift':
                name = gift.translate('gift_type')
            else:
                name = gift.translate('sponsorship_gift_type') + ' ' + _(
                    'Gift')
            name += ' [' + gift.sponsorship_id.name + ']'
            gift.name = name

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Try to find existing gifts before creating a new one. """
        gift = self.search([
            ('sponsorship_id', '=', vals['sponsorship_id']),
            ('gift_type', '=', vals['gift_type']),
            ('attribution', '=', vals['attribution']),
            ('sponsorship_gift_type', '=', vals['sponsorship_gift_type']),
            ('state', 'in', ['draft', 'verify', 'error'])
        ], limit=1)
        if gift:
            # Update gift invoice lines
            invl_write = list()
            for line_write in vals['invoice_line_ids']:
                if line_write[0] == 6:
                    # Avoid replacing all line_ids => change (6, 0, ids) to
                    # [(4, id), (4, id), ...]
                    invl_write.extend([(4, id) for id in line_write[2]])
                else:
                    invl_write.append(line_write)
            gift.write({'invoice_line_ids': invl_write})

        else:
            # If a gift for the same partner is to verify, put as well
            # the new one to verify.
            partner_id = self.env['recurring.contract'].browse(
                vals['sponsorship_id']).partner_id.id
            gift_to_verify = self.search_count([
                ('partner_id', '=', partner_id),
                ('state', '=', 'verify')
            ])
            if gift_to_verify:
                vals['state'] = 'verify'
            gift = super(SponsorshipGift, self).create(vals)
            gift._create_gift_message()

        return gift

    @api.multi
    def unlink(self):
        for gift in self:
            if gift.state not in ('verify', 'draft'):
                raise Warning(_("You cannot delete a processed gift."))
            if gift.message_id:
                gift.message_id.unlink()
        return super(SponsorshipGift, self).unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def create_from_invoice_line(self, invoice_line):
        """
        Creates a sponsorship.gift record from an invoice_line
        :param invoice_line: account.invoice.line record
        :return: sponsorship.gift record
        """

        gift_vals = self.get_gift_values_from_product(invoice_line)
        if not gift_vals:
            return False

        gift = self.create(gift_vals)
        if not gift.is_eligible():
            gift.state = 'verify'
        return gift

    @api.model
    def get_gift_values_from_product(self, invoice_line):
        """
        Converts a product into sponsorship.gift values
        :param: invoice_line: account.invoice.line record
        :return: dictionary of sponsorship.gift values
        """
        instructions = False
        product = invoice_line.product_id
        sponsorship = invoice_line.contract_id
        if not product.categ_name == GIFT_CATEGORY:
            return False

        if _(product.with_context(lang=invoice_line.create_uid.lang)
                .name).lower() not in invoice_line.name.lower():
            instructions = invoice_line.name

        gift_vals = self.get_gift_types(product)
        if gift_vals:
            gift_vals.update({
                'sponsorship_id': sponsorship.id,
                'invoice_line_ids': [(4, invoice_line.id)],
                'instructions': instructions,
            })

        return gift_vals

    @api.multi
    def is_eligible(self):
        self.ensure_one()
        minimum_amount = 1.0
        maximum_amount = 1000.0

        this_amount = self.amount
        if this_amount < minimum_amount:
            return False

        sponsorship = self.sponsorship_id

        # search other gifts for the same sponsorship.
        # we will compare the date with the first january of the current year
        firstJanuaryOfThisYear = fields.Date().today()[0:4] + '-01-01'

        other_gifts = self.search([
            ('sponsorship_id', '=', sponsorship.id),
            ('date_partner_paid', '>=', firstJanuaryOfThisYear),
        ])

        total_amount = this_amount
        if other_gifts:
            total_amount += sum(other_gifts.mapped('amount'))

        return total_amount < maximum_amount

    @api.model
    def get_gift_types(self, product):
        """ Given a product, returns the correct values
        of a gift for GMC.

        :return: dictionary of sponsorship.gift values
        """
        gift_type_vals = dict()
        product = product.with_context(lang='en_US')
        if product.name == GIFT_NAMES[0]:
            gift_type_vals.update({
                'gift_type': 'Beneficiary Gift',
                'attribution': 'Sponsorship',
                'sponsorship_gift_type': 'Birthday',
            })
        elif product.name == GIFT_NAMES[1]:
            gift_type_vals.update({
                'gift_type': 'Beneficiary Gift',
                'attribution': 'Sponsorship',
                'sponsorship_gift_type': 'General',
            })
        elif product.name == GIFT_NAMES[2]:
            gift_type_vals.update({
                'gift_type': 'Family Gift',
                'attribution': 'Sponsored Child Family',
            })
        elif product.name == GIFT_NAMES[3]:
            gift_type_vals.update({
                'gift_type': 'Project Gift',
                'attribution': 'Center Based Programming',
            })
        elif product.name == GIFT_NAMES[4]:
            gift_type_vals.update({
                'gift_type': 'Beneficiary Gift',
                'attribution': 'Sponsorship',
                'sponsorship_gift_type': 'Graduation/Final',
            })

        return gift_type_vals

    def on_send_to_connect(self):
        self.write({'state': 'open'})

    @api.multi
    def on_gift_sent(self, data):
        data.update({
            'state': 'fund_due',
            'gmc_state': 'sent'
        })
        self.write(data)

    @api.model
    def process_commkit(self, commkit_data):
        ''' This function is automatically executed when an Update Gift
        Message is received. It will convert the message from json to odoo
        format and then update the concerned records
        :param commkit_data contains the data of the message (json)
        :return list of gift ids which are concerned by the message '''

        gift_update_mapping = mapping.new_onramp_mapping(
                                                self._name,
                                                self.env,
                                                'create_update_gifts')

        # actually commkit_data is a dictionary with a single entry which
        # value is a list of dictionary (for each record)
        GiftUpdateRequestList = commkit_data['GiftUpdateRequestList']
        gift_ids = []
        # For each dictionary, we update the corresponding record
        for GiftUpdateRequest in GiftUpdateRequestList:
            vals = gift_update_mapping.\
                get_vals_from_connect(GiftUpdateRequest)
            gift_id = vals['id']
            gift_ids.append(gift_id)
            gift_record = self.env['sponsorship.gift'].browse([gift_id])
            gift_record.write(vals)

        return gift_ids

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def view_invoices(self):
        return {
            'name': _("Invoices"),
            'domain': [('id', 'in', self.invoice_line_ids.mapped(
                'invoice_id').ids)],
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'target': 'current',
            'context': self.with_context({
                'form_view_ref': 'account.invoice_form',
            }).env.context
        }

    @api.multi
    def action_ok(self):
        self.write({'state': 'draft'})
        self.mapped('message_id').write({'state': 'new'})

    @api.multi
    def action_verify(self):
        self.write({'state': 'verify'})
        self.mapped('message_id').write({'state': 'postponed'})

    @api.multi
    def action_cancel(self):
        """ Cancel Invoices and delete Gifts. """
        invoices = self.mapped('invoice_line_ids.invoice_id')
        self.env['account.move.line']._remove_move_reconcile(
            invoices.mapped('payment_ids.reconcile_id.line_id.id'))
        invoices.signal_workflow('invoice_cancel')
        self.mapped('message_id').unlink()
        return self.unlink()

    @api.onchange('gift_type')
    def onchange_gift_type(self):
        if self.gift_type == 'Beneficiary Gift':
            self.attribution = 'Sponsorship'
        elif self.gift_type == 'Family Gift':
            self.attribution = 'Sponsored Child Family'
        elif self.gift_type == 'Project Gift':
            self.attribution = 'Center Based Programming'

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _create_gift_message(self):
        for gift in self:
            # message_center_compassion/models/gmc_messages
            message_obj = self.env['gmc.message.pool']

            action_id = self.env.ref(
                'gift_compassion.create_gift').id

            message_vals = {
                'action_id': action_id,
                'object_id': gift.id,
                'partner_id': gift.partner_id.id,
                'child_id': gift.child_id.id,
            }
            gift.message_id = message_obj.create(message_vals)
