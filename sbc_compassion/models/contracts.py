# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, fields, models


class Contracts(models.Model):
    """ Add correspondence information in contracts
    """

    _inherit = 'recurring.contract'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    reading_language = fields.Many2one(
        'res.lang.compassion', 'Preferred language', required=True,
        default=lambda self: self.env.ref(
            'sbc_compassion.lang_compassion_german'))
    writing_language = fields.Many2one(
        'res.lang.compassion', related='reading_language',
        help='By now equals to reading language. Could be used in the future')
    child_letter_ids = fields.Many2many(
        'sponsorship.correspondence', string='Child letters',
        compute='_get_letters')
    sponsor_letter_ids = fields.Many2many(
        'sponsorship.correspondence', string='Sponsor letters',
        compute='_get_letters')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_letters(self):
        """ Retrieve correspondence of sponsorship contracts. """
        for sponsorship in self:
            letters_obj = self.env['sponsorship.correspondence']
            letters = letters_obj.search([
                ('sponsorship_id', '=', sponsorship.id)])
            sponsorship.child_letter_ids = letters.filtered(
                lambda l: l.direction == 'Beneficiary To Supporter')
            sponsorship.sponsor_letter_ids = letters.filtered(
                lambda l: l.direction == 'Supporter To Beneficiary')

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('correspondant_id', 'child_id')
    def onchange_relationship(self):
        """ Define the preferred reading language for the correspondent.
            1. Sponsor main language if child speaks that language
            2. Any language spoken by both sponsor and child other than
               English
            3. English, if Sponsor understands it
            4. Sponsor main language
        """
        for sponsorship in self:
            if sponsorship.correspondant_id and sponsorship.child_id:
                sponsor = sponsorship.correspondant_id
                child_languages = sponsorship.child_id.project_id.country_id.\
                    spoken_lang_ids
                sponsor_languages = sponsor.spoken_lang_ids
                lang_obj = self.env['res.lang.compassion']
                sponsor_main_lang = lang_obj.search([
                    ('lang_id.code', '=', sponsor.lang)])
                if sponsor_main_lang in child_languages:
                    sponsorship.reading_language = sponsor_main_lang
                else:
                    english = self.env.ref(
                        'sbc_compassion.lang_compassion_english')
                    common_langs = (child_languages &
                                    sponsor_languages) - english
                    if common_langs:
                        sponsorship.reading_language = common_langs[0]
                    elif english in sponsor_languages:
                        sponsorship.reading_language = english
                    else:
                        sponsorship.reading_language = sponsor_main_lang
