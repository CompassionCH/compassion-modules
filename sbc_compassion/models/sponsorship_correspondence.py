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


class CorrespondenceType(models.Model):
    _name = 'sponsorship.correspondence.type'

    name = fields.Char(required=True)


class SponsorshipCorrespondence(models.Model):
    """ This class holds the data of a Communication Kit between
    a child and a sponsor.
    """
    _name = 'sponsorship.correspondence'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # 1. Mandatory and basic fields
    ###############################
    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship', required=True, domain=[
            ('state', 'not in', ['draft', 'cancelled'])])
    name = fields.Char(compute='_set_name')
    correspondant_id = fields.Many2one(
        related='sponsorship_id.correspondant_id', store=True)
    child_id = fields.Many2one(related='sponsorship_id.child_id', store=True)
    # Field used for identifying correspondence by GMC
    kit_id = fields.Integer('Kit id', copy=False, readonly=True)
    direction = fields.Selection(
        selection=[
            ('Supporter To Beneficiary', _('Supporter to beneficiary')),
            ('Beneficiary To Supporter', _('Beneficiary to supporter'))],
        required=True, default='Supporter To Beneficiary')
    communication_type_ids = fields.Many2many(
        'sponsorship.correspondence.type',
        'sponsorship_correspondence_type_relation',
        'correspondence_id', 'type_id',
        'Communication type',
        default=lambda self: [(4, self.env.ref(
            'sbc_compassion.correspondence_type_supporter').id)])
    state = fields.Selection(
        'get_states', default='Letter scanned in from GP')

    # 2. Attachments and scans
    ##########################
    letter_image = fields.Many2one('ir.attachment')
    letter_format = fields.Selection([
        ('pdf', 'pdf'), ('tiff', 'tiff')])
    physical_attachments = fields.Selection(selection=[
        ('sent_by_mail', _('Sent by mail')),
        ('not_sent', _('Not sent'))])
    attachments_description = fields.Text()
    template_id = fields.Many2one(
        'sponsorship.correspondence.template', 'Template')

    # 3. Letter language and text information
    #########################################
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
    original_text = fields.Text()
    translated_text = fields.Text()
    source = fields.Selection(selection=[
        ('letter', _('Letter')),
        ('email', _('E-Mail')),
        ('website', _('Compassion website'))], default='letter')

    # 4. Additional information
    ###########################
    status_date = fields.Date()
    scanned_date = fields.Date(default=fields.Date.today())
    relationship = fields.Selection([
        ('Sponsor', _('Sponsor')),
        ('Encourager', _('Encourager'))], default='Sponsor')
    mandatory_review = fields.Boolean(compute='_set_partner_review',
                                      readonly=False, store=True)
    rework_reason = fields.Char()
    rework_comments = fields.Text()
    letter_url = fields.Char()

    # 5. SQL Constraints
    ####################
    _sql_constraints = [
        ('kit_id',
         'unique(kit_id)',
         _('The kit id already exists in database.'))
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def get_states(self):
        """ Returns the possible states, based on letter direction. """
        child_letter_states = [
            ('Letter ready to be printed', _('Ready to be printed')),
            ('Letter printed and sent to ICP', _('Sent to ICP')),
            ('Letter in FO transcribing, translation and content check '
             'process', _('FO content check')),
            ('Letter scanned in from FO', _('Scanned in from FO')),
            ('Letter in SDL FO translation queue', _('SDL FO Translation')),
            ('Letter in quality check queue', _('Quality Check Queue')),
            ('Letter in quality check process', _('Quality Check Process')),
            ('Letter translation and quality check complete',
             _('Quality Check Done')),
            ('Letter in SDL GP translation queue', _('To Translate')),
            ('Letter in composition process', _('Composition Process')),
            ('Letter published to GP', _('Published')),
            ('Letter marked for rework', _('Marked for rework')),
            ('Letter rejected', _('Rejected')),
        ]
        sponsor_letter_states = [
            ('Letter scanned in from GP', _('Scanned in')),
            ('Letter in SDL GP translation queue', _('To Translate')),
            ('Letter in quality check queue', _('Quality Check Queue')),
            ('Letter in quality check process', _('Quality Check Process')),
            ('Letter translation and quality check complete',
             _('Quality Check Done')),
            ('Letter in SDL FO translation queue', _('SDL FO Translation')),
            ('Letter in composition process', _('Composition Process')),
            ('Letter printed and sent to ICP', _('Sent to ICP')),
            ('Letter marked for rework', _('Marked for rework')),
            ('Letter rejected', _('Rejected')),
        ]
        direction = 'Supporter To Beneficiary'
        try:
            direction = self.direction
        except AttributeError:
            direction = self.env.context.get('default_direction', direction)
        if direction == 'Beneficiary To Supporter':
            return child_letter_states
        else:
            return sponsor_letter_states

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
        if self.sponsorship_id and self.communication_type_ids:
            self.name = self.communication_type_ids[0].name + ' (' + \
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

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def button_import(self):
        return
