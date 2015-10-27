# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Emmanuel Mathier
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import magic
import base64

from openerp import fields, models, api, exceptions, _


class SponsorshipCorrespondence(models.Model):
    """ This class holds the data of a Communication Kit between
    a child and a sponsor.
    """

    _name = 'sponsorship.correspondence'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship', required=True, domain=[
            ('state', 'not in', ['draft', 'cancelled'])])
    name = fields.Char(compute='_set_name')
    correspondant_id = fields.Many2one(
        related='sponsorship_id.correspondant_id', store=True)
    child_id = fields.Many2one(related='sponsorship_id.child_id', store=True)
    # Field used for identifying correspondence
    kit_id = fields.Integer('Kit id', copy=False, readonly=True)
    direction = fields.Selection(
        selection=[
            ('Supporter To Beneficiary', _('Supporter to beneficiary')),
            ('Beneficiary To Supporter', _('Beneficiary to supporter'))],
        required=True, default='Supporter To Beneficiary')
    communication_type = fields.Selection(
        'get_communication_types', required=True, default='Supporter Letter')
    state = fields.Selection(selection=[
        ('new', _('New')),
        ('to_translate', _('To translate')),
        ('translated', _('Translated')),
        ('quality_checked', _('Quality checked')),
        ('rejected', _('Rejected')),
        ('sent', _('Sent')),
        ('delivered', _('Delivered'))], default='new')
    status_date = fields.Date()
    scanned_date = fields.Date()
    relationship = fields.Selection([
        ('Sponsor', _('Sponsor')),
        ('Encourager', _('Encourager'))], default='Sponsor')
    mandatory_review = fields.Boolean(compute='_set_partner_review',
                                      readonly=False, store=True)
    letter_image = fields.Many2one('ir.attachment', required=True)
    letter_format = fields.Selection([
        ('pdf', 'pdf'), ('tiff', 'tiff')])
    # letter_image_preview = fields.Many2one('ir.attachment',
    # compute='_set_preview')
    physical_attachments = fields.Selection(selection=[
        ('sent_by_mail', _('Sent by mail')),
        ('not_sent', _('Not sent'))])
    attachments_description = fields.Text()
    supporter_languages_ids = fields.Many2many(
        related='correspondant_id.spoken_langs_ids', readonly=True)
    beneficiary_language_ids = fields.Many2many(
        related='child_id.project_id.country_id.spoken_langs_ids',
        readonly=True)
    # First spoken lang of partner
    original_language_id = fields.Many2one(
        'res.lang.compassion', compute='_set_languages',
        inverse='_change_language', store=True)
    destination_language_id = fields.Many2one(
        'res.lang.compassion', compute='_set_languages',
        inverse='_change_language', store=True)
    template_id = fields.Many2one(
        'sponsorship.correspondence.template', 'Template')
    original_text = fields.Text()
    translated_text = fields.Text()
    source = fields.Selection(selection=[
        ('letter', _('Letter')),
        ('email', _('E-Mail')),
        ('website', _('Compassion website'))], default='letter')

    _sql_constraints = [
        ('kit_id',
         'unique(kit_id)',
         _('The kit id already exists in database.'))
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def get_communication_types(self):
        return [
            ('Beneficiary Initiated Letter', _('Beneficiary Initiated')),
            ('Final Letter', _('Final Letter')),
            ('Large Gift Thank You Letter', _('Large Gift Thank You')),
            ('Small Gift Thank You Letter', _('Small Gift Thank You')),
            ('New Sponsor Letter', _('New Sponsor Letter')),
            ('Reciprocal Letter', _('Reciprocal Letter')),
            ('Scheduled Letter', _('Scheduled')),
            ('Supporter Letter', _('Supporter Letter')),
        ]

    @api.depends('sponsorship_id')
    def _set_name(self):
        if self.sponsorship_id and self.communication_type:
            self.name = self.communication_type + ' (' + \
                self.sponsorship_id.partner_codega + " - " + \
                self.child_id.code + ')'
        else:
            self.name = _('New correspondence')

    @api.depends('sponsorship_id', 'direction')
    def _set_languages(self):
        if self.direction == 'Supporter To Beneficiary':
            if self.correspondant_id.spoken_langs_ids:
                self.original_language_id = self.correspondant_id\
                    .spoken_langs_ids[0]
            if self.child_id.project_id.country_id.spoken_langs_ids:
                self.destination_language_id = self.child_id.project_id\
                    .country_id.spoken_langs_ids[0]
        if self.direction == 'Beneficiary To Supporter':
            if self.child_id.project_id.country_id.spoken_langs_ids:
                self.original_language_id = self.child_id.project_id\
                    .country_id.spoken_langs_ids[0]
            if self.correspondant_id.spoken_langs_ids:
                self.destination_language_id = self.correspondant_id\
                    .spoken_langs_ids[0]

    @api.depends('sponsorship_id')
    def _set_partner_review(self):
        if self.correspondant_id.mandatory_review:
            self.mandatory_review = True
        else:
            self.mandatory_review = False

    def button_import(self):
        return

    def _change_language(self):
        return True

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Letter image field is in binary so we convert to ir.attachment """
        # Write scanned_date for supporter letters
        if vals.get('direction') == 'Supporter To Beneficiary':
            vals['scanned_date'] = fields.Date.today()

        letter_image = vals.get('letter_image')
        attachment = False
        if letter_image and not isinstance(letter_image, (int, long)):
            # Detect filetype
            ftype = magic.from_buffer(base64.b64decode(letter_image), True)
            if 'pdf' in ftype:
                type = '.pdf'
            elif 'tiff' in ftype:
                type = '.tiff'
            else:
                raise exceptions.Warning(
                    _('Unsupported file format'),
                    _('You can only attach tiff or pdf files'))
            attachment = self.env['ir.attachment'].create({
                'name': 'New letter',
                'res_model': self._name,
                'datas': letter_image})
            vals['letter_image'] = attachment.id

        letter = super(SponsorshipCorrespondence, self).create(vals)
        if attachment:
            attachment.write({
                'name': letter.scanned_date + '_' + letter.name + type,
                'datas_fname': letter.name,
                'res_id': letter.id})
        return letter

    @api.multi
    def write(self, vals):
        """ Keep track of state changes. """
        if 'state' in vals:
            vals['status_date'] = fields.Date.today()
        return super(SponsorshipCorrespondence, self).write(vals)
