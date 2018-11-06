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

    related_active_sponsorships = fields.One2many(
        "recurring.contract", compute='_compute_related_active_sponsorship')
    related_sponsorships = fields.One2many(
        "recurring.contract", compute='_compute_related_sponsorship')

    # sr -> Sponsorship Report
    sr_sponsorship = fields.Integer('Number of sponsorship',
                                    compute='_compute_sr_sponsorship',
                                    help='Count only the sponsorships who '
                                         'are fully managed or those who are '
                                         'paid (not the correspondent).')
    sr_nb_b2s_letter = fields.Integer('Number of letters to sponsor',
                                      compute='_compute_b2s_letter')
    sr_nb_s2b_letter = fields.Integer('Number of letters to beneficiary',
                                      compute='_compute_s2b_letter')
    sr_nb_boy = fields.Integer('Number of boys', compute='_compute_boy')
    sr_nb_girl = fields.Integer('Number of girls', compute='_compute_girl')
    sr_time_fcp = fields.Integer('Total hour spent at the FCP',
                                 compute='_compute_time_scp')
    sr_nb_meal = fields.Integer('Number of meals served',
                                compute='_compute_meal')
    sr_nb_bible = fields.Integer('Number of bibles distributed',
                                 compute='_compute_nb_bible')
    sr_nb_medic_check = fields.Integer('Number of given medical checks',
                                       compute='_compute_medic_check')
    sr_total_donation = fields.Monetary('Invoices',
                                        compute='_compute_total_donation')
    sr_total_gift = fields.Integer('Gift',
                                   compute='_compute_total_gift')

    @api.multi
    def _compute_related_sponsorship(self):
        for partner in self:
            sponsorships = partner.sponsorship_ids
            sponsorships |= partner.member_ids.mapped('sponsorship_ids')
            partner.related_sponsorships = sponsorships

    @api.multi
    def _compute_related_active_sponsorship(self):
        for partner in self:
            sponsorships = partner.related_sponsorships
            partner.related_active_sponsorships = sponsorships.filtered(
                'is_active')

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
    def _compute_sr_sponsorship(self):
        for partner in self:
            partner.sr_sponsorship = len(partner.related_active_sponsorships)

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
            partner.sr_nb_boy = len(partner.related_active_sponsorships.mapped(
                'child_id').filtered(lambda r: r.gender == 'M'))

    @api.multi
    def _compute_girl(self):
        for partner in self:
            partner.sr_nb_girl = len(
                partner.related_active_sponsorships.mapped(
                    'child_id').filtered(lambda r: r.gender == 'F'))

    @api.multi
    def _compute_time_scp(self):
        def get_time_in_scp(sponsorship):
            nb_weeks = sponsorship.contract_duration / 7.
            country = sponsorship.child_id.field_office_id
            return nb_weeks * country.fcp_hours_week

        for partner in self:
            total_day = sum(
                partner.related_sponsorships.mapped(get_time_in_scp))
            partner.sr_time_fcp = total_day

    @api.multi
    def _compute_meal(self):
        def get_nb_meal(sponsorship):
            nb_weeks = sponsorship.contract_duration / 7.
            country = sponsorship.child_id.field_office_id
            return nb_weeks * country.fcp_meal_week

        for partner in self:
            total_meal = sum(
                partner.related_sponsorships.filtered('global_id').mapped(
                    get_nb_meal))
            partner.sr_nb_meal = total_meal

    @api.multi
    def _compute_medic_check(self):
        def get_nb_check(sponsorship):
            nb_year = sponsorship.contract_duration / 365
            country = sponsorship.child_id.field_office_id
            return nb_year * country.fcp_medical_check

        for partner in self:
            total_check = sum(
                partner.related_sponsorships.filtered('global_id').mapped(
                    get_nb_check))
            partner.sr_nb_medic_check = total_check

    @api.multi
    def _compute_nb_bible(self):
        for partner in self:
            total_bible = len(
                partner.related_sponsorships.filtered('global_id'))
            partner.sr_nb_bible = total_bible

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
                 ('last_payment', '>=', _partner.start_period)
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
