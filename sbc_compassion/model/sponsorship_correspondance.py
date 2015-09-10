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

    """ This class upgrade the partners to match Compassion needs.
    """

    _name = 'sponsorship.correspondence'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship', required=True, store=True)
    name = fields.Text('name')
    # Field used for identifying correspondence
    kit_id = fields.Integer('Kit id', copy=False, store=True)

    letter_type = fields.Selection(selection=[
        ('S2B', _('Sponsor to beneficiary')),
        ('B2S', _('Beneficiary to sponsor'))], store=True)
    communication_type = fields.Selection(selection=[
        ('scheduled', _('Scheduled')),
        ('response', _('Response')),
        ('thank_you', _('Thank you')),
        ('third_party', _('Third party')),
        ('christmas', _('Christmas')),
        ('introduction', _('Introduction'))], store=True)
    state = fields.Selection(selection=[
        ('new', _('New')),
        ('to_translate', _('To translate')),
        ('translated', _('Translated')),
        ('quality_checked', _('Quality checked')),
        ('rejected', _('Rejected')),
        ('sent', _('Sent')),
        ('delivered', _('Delivered'))], store=True)
    is_encourager = fields.Boolean(default=False, store=True)
    # Flag if the sponsor has wrote freakly words
    mandatory_review = fields.Boolean(
        related='sponsorship_id.correspondant_id.mandatory_review')
    letter_image = fields.Binary()
    attachments = fields.Many2many('ir.attachment')
    physical_attachments = fields.Selection(selection=[
        ('none', _('None')),
        ('sent_by_mail', _('Sent by mail')),
        ('not_sent', _('Not sent'))], store=True)
    attachments_description = fields.Text(store=True)
    supporter_language = fields.Many2many(
        related='sponsorship_id.correspondant_id.spoken_langs_ids')
    beneficiary_language = fields.Many2many(
        related='sponsorship_id.child_id.project_id.country_id.\
spoken_langs_ids')
    # First spoken lang of partner
    current_language = fields.Many2one('res.lang.compassion', store=True)
    template_id = fields.Integer(store=True)
    original_text = fields.Text(store=True)
    translated_text = fields.Text(store=True)
    source = fields.Selection(selection=[
        ('letter', _('Letter')),
        ('email', _('E-Mail')),
        ('website', _('Compassion website'))], store=True)

    _sql_constraints = [
        ('kit_id',
         'unique(kit_id)',
         _('The kit id already exists in database.'))
    ]

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################

    # On sponsorship_id change
    # Get sponsorship name and first spoken lang of the correspondent
    @api.onchange('sponsorship_id')
    def check_change(self):
        self.name = str(
            self.sponsorship_id.partner_codega) + " - " + str(
                self.sponsorship_id.child_id.code)
        if self.sponsorship_id.correspondant_id.spoken_langs_ids:
            self.current_language = self.sponsorship_id.correspondant_id\
                .spoken_langs_ids[0]
