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
from pyPdf import PdfFileWriter, PdfFileReader
from io import BytesIO

from .correspondence_page import BOX_SEPARATOR, PAGE_SEPARATOR


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
        required=True, default='Supporter To Beneficiary')
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
        ('pdf', 'pdf'), ('tiff', 'tiff'), ('zip', 'zip')],
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
    translation_language_id = fields.Many2one(
        'res.lang.compassion', 'Translation language',
        oldname='destination_language_id')
    original_text = fields.Text(
        compute='_compute_original_text',
        inverse='_inverse_original')
    english_text = fields.Text(
        compute='_compute_english_translated_text',
        inverse='_inverse_english')
    translated_text = fields.Text(
        compute='_compute_translated_text',
        inverse='_inverse_translated')
    page_ids = fields.One2many(
        'correspondence.page', 'correspondence_id')
    nbr_pages = fields.Integer(
        string='Number of pages', compute='_compute_nbr_pages')
    b2s_layout_id = fields.Many2one('correspondence.b2s.layout', 'B2S layout')

    # 4. Additional information
    ###########################
    status_date = fields.Datetime(default=fields.Datetime.now)
    scanned_date = fields.Date(default=fields.Date.today)
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
        for letter in self:
            letter.original_text = letter._get_text('original_text')

    @api.depends('page_ids')
    def _compute_translated_text(self):
        for letter in self:
            letter.translated_text = letter._get_text('translated_text')

    @api.depends('page_ids')
    def _compute_english_translated_text(self):
        for letter in self:
            letter.english_text = letter._get_text('english_translated_text')

    @api.depends('page_ids')
    def _compute_nbr_pages(self):
        for letter in self:
            letter.nbr_pages = len(letter.page_ids)

    @api.one
    def _inverse_original(self):
        self._set_text('original_text', self.original_text)

    @api.one
    def _inverse_english(self):
        self._set_text('english_translated_text', self.english_text)

    @api.one
    def _inverse_translated(self):
        self._set_text('translated_text', self.translated_text)

    @api.one
    def _set_text(self, field, text):
        # Try to put text in correct pages (the text should contain
        # separators).
        if not text:
            return
        pages_text = text.split(PAGE_SEPARATOR)
        if self.page_ids:
            if len(pages_text) <= len(self.page_ids):
                for i in xrange(0, len(pages_text)):
                    setattr(self.page_ids[i], field, pages_text[i].strip('\n'))
            else:
                for i in xrange(0, len(self.page_ids)):
                    setattr(self.page_ids[i], field, pages_text[i].strip('\n'))
                last_page_text = getattr(self.page_ids[i], field)
                last_page_text += '\n\n' + '\n\n'.join(pages_text[i+1:])
        else:
            for i in xrange(0, len(pages_text)):
                self.page_ids.create({
                    field: pages_text[i].strip('\n'),
                    'correspondence_id': self.id})

    def _get_text(self, source_text):
        """ Gets the desired text (original/translated) from the pages. """
        txt = self.page_ids.filtered(source_text).mapped(source_text)
        return ('\n'+PAGE_SEPARATOR+'\n').join(txt)

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
            elif 'zip' in ftype:
                letter.letter_format = 'zip'

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
            if not vals.get('translation_language_id'):
                vals['translation_language_id'] = vals.get(
                    'original_language_id')
        else:
            vals['status_date'] = fields.Datetime.now()
            if 'communication_type_ids' not in vals:
                vals['communication_type_ids'] = [(
                    4, self.env.ref(
                        'sbc_compassion.correspondence_type_scheduled').id)]
            # Allows manually creating a B2S letter
            if vals.get('state',
                        'Received in the system') == 'Received in the system':
                vals['state'] = 'Published to Global Partner'

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
            # Set the correct number of pages
            image_data = base64.b64decode(attachment.datas)
            image_pdf = PdfFileReader(BytesIO(image_data))
            if letter.nbr_pages < image_pdf.numPages:
                pages = list()
                for i in range(letter.nbr_pages, image_pdf.numPages):
                    pages.append((0, 0, {'correspondence_id': letter.id}))
                letter.write({'page_ids': pages})
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

    @api.multi
    def unlink(self):
        for letter in self:
            if letter.kit_identifier or letter.state == 'Global Partner ' \
                                                        'translation queue':
                raise exceptions.Warning(
                    _("You cannot delete a letter which is in "
                      "translation or already sent to GMC."))
        super(Correspondence, self).unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def compose_letter_image(self):
        """
        Puts the translated text of a letter inside the original image given
        the child letter layout.
        :return: True if the composition succeeded, False otherwise
        """
        self.ensure_one()
        layout = self.b2s_layout_id
        image_data = base64.b64decode(self.letter_image.datas)
        text = self.translated_text or self.english_text
        if not text or not layout:
            return False

        # Read the existing PDF of the letter
        existing_pdf = PdfFileReader(BytesIO(image_data))
        # Prepare a new composed PDF
        final_pdf = PdfFileWriter()
        # Holds the text that cannot fit in the box
        remaining_text = ''
        additional_pages_header = 'Page '
        if self.correspondant_id.lang == 'de_DE':
            additional_pages_header = 'Seite '
        elif self.correspondant_id.lang == 'it_IT':
            additional_pages_header = 'Pagina '

        def get_chars(t): return "".join(re.findall("[a-zA-Z]+", t))

        for i in xrange(0, existing_pdf.numPages):
            text = ''
            if len(self.page_ids) > i:
                page = self.page_ids[i]
                text = page.translated_text or page.english_translated_text \
                    or ''
            if len(get_chars(remaining_text + text)) < 3:
                # Page with less than 3 characters are not considered valid
                # for translation. Just keep the original page.
                final_pdf.addPage(existing_pdf.getPage(i))
                continue

            # Take the boxes depending on which page we handle
            boxes = False
            if i == 0:
                boxes = layout.page_1_box_ids
            elif i == 1:
                boxes = layout.page_2_box_ids
            if not boxes:
                # For subsequent pages, translation will go at the end of pdf.
                final_pdf.addPage(existing_pdf.getPage(i))
                if remaining_text:
                    remaining_text += '\n\n' + additional_pages_header +\
                        str(i+1) + ':\n' + text
                else:
                    remaining_text = additional_pages_header + str(i+1) +\
                                     ':\n' + text
                continue
            box_texts = text.split(BOX_SEPARATOR)
            if len(box_texts) > len(boxes):
                # There should never be more text than expected by the
                # layout. Try with only one text.
                if len(boxes) == 1:
                    box_texts = [text.replace(BOX_SEPARATOR, '\n\n')]
                else:
                    return False

            # Construct new PDF for the current page
            page_output = PdfFileWriter()
            page_output.addPage(existing_pdf.getPage(i))

            # Compose the text for each box inside the page
            for j in xrange(0, len(box_texts)):
                text = remaining_text + box_texts[j]
                box = boxes[j]
                translation_pdf, remaining_text = box.get_pdf(text)

                # Check that the text can fit in the box
                if remaining_text:
                    # Add a return to separate remaining text from following
                    remaining_text += '\n\n'
                    # Log when text is too long to see if that happens a lot
                    self.message_post(
                        'Translation went out of the translation box',
                        'Translation too long')

                # Merge the translation on the existing page
                page = page_output.getPage(j)
                page.mergePage(translation_pdf.getPage(0))
                page_output.addPage(page)

            # Write the last version of the page into final pdf
            final_pdf.addPage(page_output.getPage(j))

        # Add pages if there is remaining text
        while remaining_text:
            box = layout.additional_page_box_id
            translation_pdf, remaining_text = box.get_pdf(remaining_text, True)
            final_pdf.addPage(translation_pdf.getPage(0))

        # Finally write the pdf back into letter_image
        output_stream = BytesIO()
        final_pdf.write(output_stream)
        output_stream.seek(0)
        self.letter_image.datas = base64.b64encode(output_stream.read())

        return True

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
                'name': letter.kit_identifier or
                letter.child_id.code + '_' + type_,
                'datas_fname': letter.name,
                'res_id': letter.id
            })
        return self.env['ir.attachment'].create(vals), type_
