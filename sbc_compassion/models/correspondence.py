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
import re

from openerp import fields, models, api, exceptions, _


class CorrespondenceType(models.Model):
    _name = 'correspondence.type'

    name = fields.Char(required=True)


class Correspondence(models.Model):
    """ This class holds the data of a Communication Kit between
    a child and a sponsor.
    """
    _name = 'correspondence'
    _inherit = [
            'mail.thread', 'ir.needaction_mixin', 'correspondence.metadata']
    _description = 'Letter'
    _order = 'status_date desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # 1. Mandatory and basic fields
    ###############################
    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship', required=True, domain=[
            ('state', 'not in', ['draft', 'cancelled'])],
        track_visibility='onchange')
    name = fields.Char(compute='_set_name')
    correspondant_id = fields.Many2one(
        related='sponsorship_id.correspondant_id', store=True)
    child_id = fields.Many2one(related='sponsorship_id.child_id', store=True)
    # Field used for identifying correspondence by GMC
    kit_identifier = fields.Char('Kit id', copy=False, readonly=True)
    direction = fields.Selection(
        selection=[
            ('Supporter To Beneficiary', _('Supporter to beneficiary')),
            ('Beneficiary To Supporter', _('Beneficiary to supporter'))],
        required=True, default='Supporter To Beneficiary', readonly=True)
    communication_type_ids = fields.Many2many(
        'correspondence.type',
        'correspondence_type_relation',
        'correspondence_id', 'type_id',
        'Communication type',
        readonly=True)
    state = fields.Selection(
        'get_states', default='Received in the system',
        track_visibility='onchange')
    s2b_state = fields.Selection('get_s2b_states', compute='_compute_states')
    b2s_state = fields.Selection('get_b2s_states', compute='_compute_states')

    # 2. Attachments and scans
    ##########################
    letter_image = fields.Many2one('ir.attachment')
    letter_format = fields.Selection([
        ('pdf', 'pdf'), ('tiff', 'tiff')],
        compute='_compute_letter_format')

    # 3. Letter language and text information
    #########################################
    supporter_languages_ids = fields.Many2many(
        related='correspondant_id.spoken_lang_ids', readonly=True)
    beneficiary_language_ids = fields.Many2many(
        related='child_id.project_id.country_id.spoken_lang_ids',
        readonly=True)
    # First spoken lang of partner
    original_language_id = fields.Many2one(
        'res.lang.compassion', 'Original language')
    destination_language_id = fields.Many2one(
        'res.lang.compassion', 'Destination language')
    original_text = fields.Text(
        compute='_compute_original_text',
        inverse='_inverse_page')
    english_text = fields.Text(
        compute='_compute_english_translated_text',
        inverse='_inverse_page')
    translated_text = fields.Text(
        compute='_compute_translated_text',
        inverse='_inverse_page')
    source = fields.Selection(selection=[
        ('letter', _('Letter')),
        ('email', _('E-Mail')),
        ('website', _('Compassion website'))], default='letter')
    page_ids = fields.One2many(
        'correspondence.page', 'correspondence_id')
    nbr_pages = fields.Integer(
        string='Number of pages', compute='_compute_nbr_pages')

    # 4. Additional information
    ###########################
    status_date = fields.Datetime(default=fields.Date.today())
    scanned_date = fields.Date(default=fields.Date.today())
    relationship = fields.Selection([
        ('Sponsor', _('Sponsor')),
        ('Encourager', _('Encourager'))], default='Sponsor')
    is_first_letter = fields.Boolean(
        compute='_compute_is_first',
        store=True,
        readonly=True,
        string='First letter from Beneficiary')
    marked_for_rework = fields.Boolean(
        readonly=True)
    rework_reason = fields.Char()
    rework_comments = fields.Text()
    original_letter_url = fields.Char()
    final_letter_url = fields.Char()
    import_id = fields.Many2one('import.letters.history')
    translator = fields.Char()
    translator_id = fields.Many2one(
        'res.partner', 'GP Translator', compute='_compute_translator',
        inverse='_set_translator', store=True)

    # 5. SQL Constraints
    ####################
    _sql_constraints = [
        ('kit_identifier',
         'unique(kit_identifier)',
         _('The kit id already exists in database.'))
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def get_states(self):
        """ Returns all the possible states. """
        return list(set(self.get_s2b_states()) | set(self.get_b2s_states()))

    @api.model
    def get_s2b_states(self):
        """ Supporter to Beneficiary states, in correct order. """
        # * means state is to be clarified by GMC
        return [
            ('Received in the system', _('Scanned in')),
            ('Global Partner translation queue', _('To Translate')),
            ('Global Partner translation process', _('Translating')),
            ('Quality check queue', _('Quality Check Queue')),
            ('Quality check process', _('Quality Check Process')),
            ('Translation and quality check complete',
             _('Quality Check Done')),
            ('Field Office translation queue', _('SDL FO Translation Queue')),
            ('Composition process', _('Composition Process')),
            ('Printed and sent to ICP', _('Sent to ICP')),
            # TODO: Check the following states with GMC to validate them...
            ('Complete Delivered', _('Delivered')),
            ('Complete Undelivered', _('Undelivered')),
            ('Undeliverable', _('Undeliverable')),
            ('Cancelled', _('Cancelled')),
            ('Exception', _('Exception')),
            ('Quality check unsuccessful', _('Quality check failed')),
        ]

    @api.model
    def get_b2s_states(self):
        """ Beneficiary to Supporter states, in correct order. """
        # * means state is to be clarified by GMC
        return [
            ('Ready to be printed', _('Ready to be printed')),  # *
            ('Field Office transcribing translation and content check '
             'process', _('FO content check')),  # *
            ('Field Office translation queue', _('SDL FO Translation Queue')),
            ('In Translation', _('SDL FO Translation')),    # *
            ('Quality check queue', _('Quality Check Queue')),
            ('Quality check process', _('Quality Check Process')),
            ('Translation and quality check complete',
             _('Quality Check Done')),  # *
            ('Global Partner translation queue', _('To Translate')),
            ('Global Partner translation process', _('Translating')),
            ('Composition process', _('Composition Process')),
            ('Published to Global Partner', _('Published')),
            # TODO: Check the following states with GMC to validate them...
            ('Quality check unsuccessful', _('Quality check unsuccessful')),
            ('Cancelled', _('Cancelled')),
            ('Exception', _('Exception')),
        ]

    @api.multi
    def _compute_states(self):
        """ Sets the internal states (s2b and b2s). """
        for letter in self:
            if letter.direction == 'Supporter To Beneficiary':
                letter.s2b_state = letter.state
            else:
                letter.b2s_state = letter.state

    @api.multi
    @api.depends('sponsorship_id')
    def _compute_is_first(self):
        """ Sets the value at true if is the first letter\
                from the beneficiary. """
        for letter in self:
            if letter.sponsorship_id:
                count = self.search_count([
                    ('sponsorship_id', '=', letter.sponsorship_id.id),
                    ('direction', '=', "Beneficiary To Supporter")
                ])
                if count == 1:
                    letter.is_first_letter = True
                else:
                    letter.is_first_letter = False

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

    @api.multi
    @api.depends('sponsorship_id')
    def _set_name(self):
        for letter in self:
            if letter.sponsorship_id and letter.communication_type_ids:
                letter.name = letter.communication_type_ids[0].name + ' (' + \
                    letter.sponsorship_id.partner_id.ref + " - " + \
                    letter.child_id.code + ')'
            else:
                letter.name = _('New correspondence')

    @api.depends('sponsorship_id')
    def _set_partner_review(self):
        for letter in self:
            if letter.correspondant_id.mandatory_review:
                letter.mandatory_review = True

    @api.depends('page_ids')
    def _compute_original_text(self):
        self.original_text = self._get_text('original_text')

    @api.depends('page_ids')
    def _compute_translated_text(self):
        self.translated_text = self._get_text('translated_text')

    @api.depends('page_ids')
    def _compute_english_translated_text(self):
        self.english_text = self._get_text('english_translated_text')

    @api.depends('page_ids')
    def _compute_nbr_pages(self):
        self.nbr_pages = len(self.page_ids)

    @api.one
    def _inverse_page(self):
        if self.page_ids:
            # Keep only the first page and remove the other
            self.page_ids[0].write({
                'original_text': self.original_text,
                'english_translated_text': self.english_text,
                'translated_text': self.translated_text,
            })
            self.page_ids[1:].unlink()
        else:
            self.page_ids.create(
                {'correspondence_id': self.id,
                 'original_text': self.original_text,
                 'english_translated_text': self.english_text,
                 'translated_text': self.translated_text},)

    def _get_text(self, source_text):
        """ Gets the desired text (original/translated) from the pages. """
        txt = self.page_ids.filtered(source_text).mapped(source_text)
        return '\n\n'.join(txt)

    def _change_language(self):
        return True

    def _compute_letter_format(self):
        for letter in self:
            ftype = magic.from_buffer(base64.b64decode(
                letter.letter_image.datas), True)
            if 'pdf' in ftype:
                letter.letter_format = 'pdf'
            elif 'tiff' in ftype:
                letter.letter_format = 'tiff'

    @api.multi
    @api.depends('translator')
    def _compute_translator(self):
        partner_obj = self.env['res.partner']
        for letter in self:
            if letter.translator:
                match = re.search('(.*)\[(.*)\]', letter.translator)
                if match:
                    (name, email) = match.group(1, 2)
                    # 1. Search by e-mail
                    partner = partner_obj.search([
                        '|', ('email', '=', email),
                        ('translator_email', '=', email)])
                    if len(partner) == 1:
                        letter.translator_id = partner
                        continue
                    # 2. Search by name
                    words = name.split()
                    partner = partner_obj.search([('name', 'like', words[0])])
                    if len(words) > 1:
                        for word in words[1:]:
                            partner = partner.filtered(
                                lambda p: word in p.name)
                            if len(partner) == 1:
                                break
                    if len(partner) == 1:
                        letter.translator_id = partner

    @api.multi
    def _set_translator(self):
        """ Sets the translator e-mail address. """
        for letter in self:
            if letter.translator:
                match = re.search('(.*)\[(.*)\]', letter.translator)
                if match:
                    letter.translator_id.translator_email = match.group(2)
                    other_letters = self.search([
                        ('translator', '=', letter.translator),
                        ('translator_id', '!=', letter.translator_id.id)])
                    other_letters._compute_translator()

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Fill missing fields.
        Letter image field is in binary so we convert to ir.attachment
        """
        if vals.get('direction',
                    'Supporter To Beneficiary') == 'Supporter To Beneficiary':
            vals['communication_type_ids'] = [(
                4, self.env.ref(
                    'sbc_compassion.correspondence_type_supporter').id)]
        else:
            vals['status_date'] = fields.Datetime.now()
            if 'communication_type_ids' not in vals:
                vals['communication_type_ids'] = [(
                    4, self.env.ref(
                        'sbc_compassion.correspondence_type_scheduled').id)]

        letter_image = vals.get('letter_image')
        attachment = False
        if letter_image and not isinstance(letter_image, (int, long)):
            attachment, type_ = self._get_letter_attachment(letter_image)
            vals['letter_image'] = attachment.id
        letter = super(Correspondence, self).create(vals)
        if attachment:
            attachment.write({
                'name': letter.scanned_date + '_' + letter.name + type_,
                'datas_fname': letter.name,
                'res_id': letter.id})
        return letter

    @api.multi
    def write(self, vals):
        """ Keep track of state changes. """
        if 'state' in vals:
            vals['status_date'] = fields.Datetime.now()
        # Allow to change letter image from the user interface
        letter_image = vals.get('letter_image')
        if letter_image and not isinstance(letter_image, (int, long)):
            self.ensure_one()
            attachment = self._get_letter_attachment(letter_image, self)[0]
            vals['letter_image'] = attachment.id
        return super(Correspondence, self).write(vals)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_letter_attachment(self, image_data, letter=None):
        """ Method that takes png/pdf binary data, create an ir.attachment
        with it and returns its id. Useful for creating the letter image.

        :returns (ir.attachement, string): attachment record, file type
        """
        # Detect filetype
        ftype = magic.from_buffer(base64.b64decode(image_data),
                                  True).lower()
        if 'pdf' in ftype:
            type_ = '.pdf'
        elif 'tiff' in ftype:
            type_ = '.tiff'
        else:
            raise exceptions.Warning(
                _('Unsupported file format'),
                _('You can only attach tiff or pdf files'))
        vals = {
            'name': 'New letter' + type_,
            'res_model': self._name,
            'datas': image_data
        }
        if letter:
            vals.update({
                'name': letter.kit_identifier + '_' + type_,
                'datas_fname': letter.name,
                'res_id': letter.id
            })
        return self.env['ir.attachment'].create(vals), type_
