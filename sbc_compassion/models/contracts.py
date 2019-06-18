# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import date, timedelta

from odoo import api, fields, models, _


class Contracts(models.Model):
    """ Add correspondence information in contracts
    """

    _inherit = 'recurring.contract'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    writing_language = fields.Many2one(
        'res.lang.compassion', related='reading_language',
        help='By now equals to reading language. Could be used in the future')
    child_letter_ids = fields.Many2many(
        'correspondence', string='Child letters',
        compute='_compute_get_letters')
    sponsor_letter_ids = fields.Many2many(
        'correspondence', string='Sponsor letters',
        compute='_compute_get_letters')
    nb_letters = fields.Integer(
        compute='_compute_get_letters'
    )
    last_letter = fields.Integer(
        'Days since sponsor wrote',
        compute='_compute_last_letter'
    )
    write_for_birthday_alert = fields.Boolean(
        help='True when child will have birthday in less than 3 months and'
             'sponsor has not written in this period.',
        compute='_compute_write_for_birthday_alert'
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_get_letters(self):
        """ Retrieve correspondence of sponsorship contracts. """
        for sponsorship in self:
            letters_obj = self.env['correspondence']
            letters = letters_obj.search([
                ('sponsorship_id', '=', sponsorship.id)])
            sponsorship.child_letter_ids = letters.filtered(
                lambda l: l.direction == 'Beneficiary To Supporter')
            sponsorship.sponsor_letter_ids = letters.filtered(
                lambda l: l.direction == 'Supporter To Beneficiary')
            sponsorship.nb_letters = len(letters)

    def _compute_last_letter(self):
        """
        Get the date of the last letter sent to the child by the sponsor and
        compute since how many days he didn't write him any letter.
        If sponsor never wrote him, return -1
        :return: int value
        """
        for contract in self:
            try:
                # Try to get days difference between today and last letter
                contract.last_letter = (
                    date.today() - fields.Date.from_string(
                        contract.sponsor_letter_ids[:1].scanned_date)).days
            except TypeError:
                contract.last_letter = -1

    def _compute_write_for_birthday_alert(self):
        for contract in self:
            if contract.last_letter == -1 or contract.last_letter > 90:
                next_birthday = fields.Date.from_string(
                    contract.child_id.birthdate).replace(year=date.today.year)

                # take next year birthday
                # if birthday already pass for this year
                if next_birthday < date.today():
                    next_birthday = next_birthday.replace(
                        year=next_birthday.year+1)

                contract.write_for_birthday_alert = \
                    next_birthday - date.today() <= timedelta(days=90)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('correspondent_id', 'child_id')
    def onchange_relationship(self):
        """ Define the preferred reading language for the correspondent.
            1. Sponsor main language if child speaks that language
            2. Any language spoken by both sponsor and child other than
               English
            3. English
        """
        for sponsorship in self:
            if sponsorship.correspondent_id and sponsorship.child_id:
                sponsor = sponsorship.correspondent_id
                child_languages = sponsorship.child_id.field_office_id.\
                    spoken_language_ids
                sponsor_languages = sponsor.spoken_lang_ids
                lang_obj = self.env['res.lang.compassion']
                sponsor_main_lang = lang_obj.search([
                    ('lang_id.code', '=', sponsor.lang)])
                if sponsor_main_lang in child_languages:
                    sponsorship.reading_language = sponsor_main_lang
                else:
                    english = self.env.ref(
                        'child_compassion.lang_compassion_english')
                    common_langs = (child_languages &
                                    sponsor_languages) - english
                    if common_langs:
                        sponsorship.reading_language = common_langs[0]
                    else:
                        sponsorship.reading_language = english

    @api.multi
    def open_letters(self):
        return {
            'name': _('Letters'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'correspondence',
            'context': self.with_context(
                group_by=False,
                search_default_sponsorship_id=self.id
            ).env.context,
            'target': 'current',
        }

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_active(self):
        """ Send letters that were on hold. """
        super(Contracts, self).contract_active()
        for contract in self.filtered(
                lambda c: 'S' in c.type and not
                c.project_id.hold_s2b_letters):
            contract.sponsor_letter_ids.reactivate_letters(
                'Sponsorship activated')
