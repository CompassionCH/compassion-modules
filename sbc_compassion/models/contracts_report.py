##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class PartnerSponsorshipReport(models.Model):
    _inherit = "res.partner"

    sr_nb_b2s_letter = fields.Integer('Number of letters to sponsor',
                                      compute='_compute_b2s_letter')
    sr_nb_s2b_letter = fields.Integer('Number of letters to beneficiary',
                                      compute='_compute_s2b_letter')

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
