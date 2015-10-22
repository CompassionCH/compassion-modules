# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import fields, models, api, _
import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../tools'))
from layout import LayoutLetter


class SponsorshipCorrespondence(models.Model):

    """ This class holds the data of a Communication Kit between
    a child and a sponsor.
    """

    _name = 'sponsorship.correspondence'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship', required=True)
    name = fields.Char(compute='_set_name')
    partner_id = fields.Many2one(
        related='sponsorship_id.correspondant_id', store=True)
    child_id = fields.Many2one(related='sponsorship_id.child_id', store=True)
    # Field used for identifying correspondence
    kit_id = fields.Integer('Kit id', copy=False, readonly=True)
    letter_type = fields.Selection(selection=[
        ('S2B', _('Sponsor to beneficiary')),
        ('B2S', _('Beneficiary to sponsor'))], required=True)
    communication_type = fields.Selection(selection=[
        ('scheduled', _('Scheduled')),
        ('response', _('Response')),
        ('thank_you', _('Thank you')),
        ('third_party', _('Third party')),
        ('christmas', _('Christmas')),
        ('introduction', _('Introduction'))])
    state = fields.Selection(selection=[
        ('new', _('New')),
        ('to_translate', _('To translate')),
        ('translated', _('Translated')),
        ('quality_checked', _('Quality checked')),
        ('rejected', _('Rejected')),
        ('sent', _('Sent')),
        ('delivered', _('Delivered'))], default='new')
    is_encourager = fields.Boolean()
    mandatory_review = fields.Boolean(compute='_set_partner_review',
                                      readonly=False, store=True)
    letter_image = fields.Many2one('ir.attachment', required=True)
    # letter_image_preview = fields.Many2one('ir.attachment',
    # compute='_set_preview')
    attachments_ids = fields.Many2many('ir.attachment')
    physical_attachments = fields.Selection(selection=[
        ('none', _('None')),
        ('sent_by_mail', _('Sent by mail')),
        ('not_sent', _('Not sent'))])
    attachments_description = fields.Text()
    supporter_languages_ids = fields.Many2many(
        related='partner_id.spoken_langs_ids',
        store=True, readonly=True)
    beneficiary_language_ids = fields.Many2many(
        related='child_id.project_id.country_id.\
spoken_langs_ids', store=True)
    # First spoken lang of partner
    original_language_id = fields.Many2one(
        'res.lang.compassion', compute='_set_original_language', store=True)
    destination_language_id = fields.Many2one(
        'res.lang.compassion', compute='_set_original_language', store=True)
    #need to change in order to avoid mutliple definition
    template_id = fields.Selection(selection=[
        (LayoutLetter.name[0], 'Template 1'),
        (LayoutLetter.name[1], 'Template 2'),
        (LayoutLetter.name[2], 'Template 3'),
        (LayoutLetter.name[3], 'Template 4'),
        (LayoutLetter.name[4], 'Template 5'),
        (LayoutLetter.name[5], 'Template 6')], required=True)
    original_text = fields.Text()
    translated_text = fields.Text()
    source = fields.Selection(selection=[
        ('letter', _('Letter')),
        ('email', _('E-Mail')),
        ('website', _('Compassion website'))])

    _sql_constraints = [
        ('kit_id',
         'unique(kit_id)',
         _('The kit id already exists in database.'))
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.depends('sponsorship_id')
    def _set_name(self):
        if self.sponsorship_id:
            self.name = str(
                self.sponsorship_id.partner_codega) + " - " + str(
                    self.child_id.code)
        else:
            self.name = _('New correspondence')

    @api.depends('sponsorship_id', 'letter_type')
    def _set_original_language(self):
        if self.letter_type == 'S2B':
            if self.partner_id.spoken_langs_ids:
                self.original_language_id = self.partner_id\
                    .spoken_langs_ids[0]
            if self.child_id.project_id.country_id.spoken_langs_ids:
                self.destination_language_id = self.child_id.project_id\
                    .country_id.spoken_langs_ids[0]
        if self.letter_type == 'B2S':
            if self.child_id.project_id.country_id.spoken_langs_ids:
                self.original_language_id = self.child_id.project_id\
                    .country_id.spoken_langs_ids[0]
            if self.partner_id.spoken_langs_ids:
                self.destination_language_id = self.partner_id\
                    .spoken_langs_ids[0]

    @api.depends('sponsorship_id')
    def _set_partner_review(self):
        if self.partner_id.mandatory_review:
            self.mandatory_review = True
        else:
            self.mandatory_review = False

    def button_import(self):
        return
