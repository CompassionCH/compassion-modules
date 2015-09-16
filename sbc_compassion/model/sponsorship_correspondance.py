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


class ResSponsorshipCorrespondence(models.Model):

    """ This class create correspondances to match Compassion needs.
    """

    _name = 'sponsorship.correspondence'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship', required=True)
    name = fields.Char('name', compute='_set_name')
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
    mandatory_review = fields.Boolean(
        related='sponsorship_id.correspondant_id.mandatory_review',
        store=True)
    letter_image = fields.Binary()
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
        related='sponsorship_id.child_id.project_id.country_id.\
spoken_langs_ids', store=True)
    # First spoken lang of partner
    original_language_id = fields.Many2one(
        'res.lang.compassion', compute='_set_current_language', store=True)
    destination_language_id = fields.Many2one('res.lang.compassion')
    template_id = fields.Selection(selection=[
        ('template_1', _('Template 1')),
        ('template_2', _('Template 2')),
        ('template_3', _('Template 3')),
        ('template_4', _('Template 4')),
        ('template_5', _('Template 5'))])
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
        self.name = str(
            self.sponsorship_id.partner_codega) + " - " + str(
                self.sponsorship_id.child_id.code)

    @api.depends('sponsorship_id')
    def _set_current_language(self):
        # Get correspondent first spoken lang
        if self.sponsorship_id.correspondant_id.spoken_langs_ids:
            self.original_language_id = self.sponsorship_id.correspondant_id\
                .spoken_langs_ids[0]
            self.destination_language_id = self.sponsorship_id\
                .correspondant_id.spoken_langs_ids[0]
