# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


# For more readability we have split "res.partner" by functionality
# pylint: disable=R7980
class PartnerSponsorshipReport(models.Model):
    _inherit = "res.partner"

    end_period = fields.Date(compute='_compute_end_period')
    start_period = fields.Date(compute='_compute_start_period')

    # sr -> Sponsorship Report
    sr_sponsorship = fields.Integer('Number of sponsorship',
                                    compute='_compute_sr_sponsorship',
                                    help='Count only the sponsorships who '
                                         'are fully managed or those who are '
                                         'paid (not the correspondent).')

    correspondent_only_sponsorship = fields.Integer('Number of sponsorships '
                                                    'as correspondent only',
                                                    compute='_compute_corres'
                                                            '_sponsorship')

    sr_nb_b2s_letter = fields.Integer('Number of letters to sponsor',
                                      compute='_compute_b2s_letter')
    sr_nb_s2b_letter = fields.Integer('Number of letters to beneficiary',
                                      compute='_compute_s2b_letter')
    sr_nb_boy = fields.Integer('Number of boys', compute='_compute_boy')
    sr_nb_girl = fields.Integer('Number of girls', compute='_compute_girl')
    sr_time_icp = fields.Integer('Total time spent at the ICP',
                                 compute='_compute_time_scp')
    sr_nb_meal = fields.Integer('Number of meals served',
                                compute='_compute_meal')
    # sr_nb_medic_check = fields.Integer('Number of given medical checks',
    #                                    compute='_compute_medic_check')
    sr_nb_bible = fields.Integer('Number of bibles distributed',
                                 related='sr_sponsorship')
    sr_total_donation = fields.Float('Invoices',
                                     compute='_compute_total_donation')
    sr_total_gift = fields.Float('Gift',
                                 compute='_compute_total_gift')

    @api.multi
    def _compute_start_period(self):
        for partner in self:
            end = fields.Date.from_string(partner.end_period)
            partner.start_period = fields.Date.to_string(
                end - relativedelta(months=12))

    @api.multi
    def _compute_end_period(self):
        today = fields.Date.today()
        for partner in self:
            partner.end_period = today

    @api.multi
    def _compute_corres_sponsorship(self):
        def get_nb_corres_sponsorship(_partner):
            return self.env['recurring.contract'].search_count(
                [('correspondent_id', '=', _partner.id),
                 ('type', 'in', ['S', 'SC']),
                 ('is_active', '=', True)])

        for partner in self:
            nb_corres_sponsorship = get_nb_corres_sponsorship(partner)
            if partner.is_church:
                for member in partner.member_ids:
                    nb_corres_sponsorship += get_nb_corres_sponsorship(member)
            partner.correspondent_only_sponsorship = nb_corres_sponsorship

    @api.multi
    def _compute_sr_sponsorship(self):
        def get_nb_sponsorship(_partner):
            return self.env['recurring.contract'].search_count(
                [('partner_id', '=', _partner.id),
                 ('type', 'in', ['S', 'SC']),
                 ('is_active', '=', True)])

        for partner in self:
            nb_sponsorship = get_nb_sponsorship(partner)
            if partner.is_church:
                for member in partner.member_ids:
                    nb_sponsorship += get_nb_sponsorship(member)
            partner.sr_sponsorship = nb_sponsorship

    @api.multi
    def _compute_b2s_letter(self):
        def get_nb_letter(_partner):
            return self.env['correspondence'].search_count(
                [('partner_id', '=', _partner.id),
                 ('direction', '=', 'Beneficiary To Supporter'),
                 ('scanned_date', '>', _partner.start_period),
                 ('scanned_date', '<=', _partner.end_period)])

        for partner in self:
            nb_letter = get_nb_letter(partner)
            if partner.is_church:
                for member in partner.member_ids:
                    nb_letter += get_nb_letter(member)
            partner.sr_nb_b2s_letter = nb_letter

    @api.multi
    def _compute_s2b_letter(self):
        def get_nb_letter(_partner):
            return self.env['correspondence'].search_count(
                [('partner_id', '=', _partner.id),
                 ('direction', '=', 'Supporter To Beneficiary'),
                 ('scanned_date', '>', _partner.start_period),
                 ('scanned_date', '<=', _partner.end_period)])

        for partner in self:
            nb_letter = get_nb_letter(partner)
            if partner.is_church:
                for member in partner.member_ids:
                    nb_letter += get_nb_letter(member)
            partner.sr_nb_s2b_letter = nb_letter

    @api.multi
    def _compute_boy(self):
        for partner in self:
            sponsorships = self.env['recurring.contract'].search([
                ('partner_id', '=', partner.id)
            ])
            count = 0
            for sponsorship in sponsorships:
                # if not correspondent only
                if sponsorship.type == 'S' and sponsorship.is_active and \
                        sponsorship.child_id.gender == 'M':
                    count += len(sponsorship.child_id)
                    if partner.is_church:
                        for member in partner.member_ids:
                            count += self.env['compassion.child'].search_count(
                                [('partner_id', '=', member.id),
                                 ('gender', '=', 'M')])
            partner.sr_nb_boy = count

    @api.multi
    def _compute_girl(self):
        for partner in self:
            sponsorships = self.env['recurring.contract'].search([
                ('partner_id', '=', partner.id)
            ])
            count = 0
            for sponsorship in sponsorships:
                # if not correspondent only
                if sponsorship.type == 'S' and sponsorship.is_active and \
                        sponsorship.child_id.gender == 'F':
                    count += len(sponsorship.child_id)
                    if partner.is_church:
                        for member in partner.member_ids:
                            count += self.env['compassion.child'].search_count(
                                [('partner_id', '=', member.id),
                                 ('gender', '=', 'F')])
            partner.sr_nb_girl = count

    @api.multi
    def _compute_time_scp(self):
        def get_time_in_scp(_partner):
            total = 0
            for contract in self.env['recurring.contract'].search(
                    [('partner_id', '=', _partner.id),
                     ('type', 'in', ['S', 'SC'])]):
                nb_weeks = contract.contract_duration / 7.
                country = contract.child_id.field_office_id
                total += nb_weeks * country.icp_hours_week
            return total

        for partner in self:
            time_to_scp = get_time_in_scp(partner)

            if partner.is_church:
                for member in partner.member_ids:
                    time_to_scp += get_time_in_scp(member)
            partner.sr_time_icp = time_to_scp

    @api.multi
    def _compute_meal(self):
        def get_nb_meal(_partner):
            total = 0
            for contract in self.env['recurring.contract'].search(
                    [('partner_id', '=', _partner.id),
                     ('type', 'in', ['S', 'SC'])]):
                nb_weeks = contract.contract_duration / 7.
                country = contract.child_id.field_office_id
                total += nb_weeks * country.icp_meal_week
            return total

        for partner in self:
            sr_meal = get_nb_meal(partner)

            if partner.is_church:
                for member in partner.member_ids:
                    sr_meal = get_nb_meal(member)
            partner.sr_nb_meal = sr_meal

    @api.multi
    def _compute_total_donation(self):
        def get_sum_invoice(_partner):
            invoices = self.env['account.invoice'].search([
                ('partner_id', '=', _partner.id),
                ('type', '=', 'out_invoice'),
                ('state', '=', 'paid'),
                ('invoice_type', 'in',
                 ['gift', 'sponsorship', 'fund']),
                ('last_payment', '<', _partner.end_period),
                ('last_payment', '>', _partner.start_period)
            ])
            return sum(invoices.mapped('amount_total'))

        for partner in self:
            sr_total_donation = get_sum_invoice(partner)
            if partner.is_church:
                for member in partner.member_ids:
                    sr_total_donation += get_sum_invoice(member)
            partner.sr_total_donation = sr_total_donation

    @api.multi
    def _compute_total_gift(self):
        def get_nb_gift(_partner):
            return self.env['account.invoice'].search_count(
                [('partner_id', '=', _partner.id),
                 ('invoice_type', '=', 'gift'),
                 ('type', '=', 'out_invoice'),
                 ('state', '=', 'paid'),
                 ('last_payment', '<', _partner.end_period),
                 ('last_payment', '>', _partner.start_period)
                 ])

        for partner in self:
            sr_total_gift = get_nb_gift(partner)
            if partner.is_church:
                for member in partner.member_ids:
                    sr_total_gift += get_nb_gift(member)
            partner.sr_total_gift = sr_total_gift

    @api.multi
    def open_sponsorship_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sponsorship Report',
            'res_model': 'res.partner',
            'view_type': 'form',
            'view_mode': 'form',
            'context': self.with_context(
                form_view_ref='sponsorship_compassion.sponsorship_report_form'
            ).env.context,
            'res_id': self.id
        }
