# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Emmanuel Mathier
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
import re
import uuid
import threading

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import config
from io import BytesIO

from .correspondence_page import BOX_SEPARATOR, PAGE_SEPARATOR
from ..tools.onramp_connector import SBCConnector

from odoo.addons.message_center_compassion.mappings import base_mapping as \
    mapping

_logger = logging.getLogger(__name__)
test_mode = config.get('test_enable')

try:
    import magic
    from pyPdf import PdfFileWriter, PdfFileReader
except ImportError:
    _logger.error('Please install magic and pypdf in order to use SBC module')


class CorrespondenceType(models.Model):
    _name = 'correspondence.type'
    _inherit = 'connect.multipicklist'
    res_model = 'correspondence'
    res_field = 'communication_type_ids'


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
    name = fields.Char(compute='_compute_name')
    partner_id = fields.Many2one(
        related='sponsorship_id.correspondent_id', store=True
    )
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
    letter_image = fields.Binary(attachment=True)
    file_name = fields.Char()
    letter_format = fields.Selection([
        ('pdf', 'pdf'), ('tiff', 'tiff'), ('zip', 'zip')],
        compute='_compute_letter_format', store=True)

    # 3. Letter language and text information
    #########################################
    supporter_languages_ids = fields.Many2many(
        related='partner_id.spoken_lang_ids', readonly=True)
    beneficiary_language_ids = fields.Many2many(
        related='child_id.project_id.field_office_id.spoken_language_ids',
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
        inverse='_inverse_set_translator', store=True)
    email = fields.Char(related='partner_id.email')
    sponsorship_state = fields.Selection(
        related='sponsorship_id.state', string='Sponsorship state')
    is_final_letter = fields.Boolean(compute='_compute_is_final_letter')
    generator_id = fields.Many2one('correspondence.s2b.generator')

    # Letter remote access
    ######################
    uuid = fields.Char(required=True, default=lambda self: self._get_uuid())
    read_url = fields.Char()

    # 5. SQL Constraints
    ####################
    _sql_constraints = [
        ('kit_identifier',
         'unique(kit_identifier)',
         _('The kit id already exists in database.'))
    ]
    # Lock
    #######
    process_lock = threading.Lock()

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
            ('Printed and sent to FCP', _('Sent to FCP')),
            ('Exception', _('Exception')),
            ('Quality check unsuccessful', _('Quality check failed')),
            ('Translation check unsuccessful', _('Translation check '
                                                 'unsuccessful')),
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
            ('Quality check unsuccessful', _('Quality check unsuccessful')),
            ('Translation check unsuccessful', _('Translation check '
                                                 'unsuccessful')),
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
    def _compute_name(self):
        for letter in self:
            if letter.sponsorship_id and letter.communication_type_ids:
                letter.name = letter.communication_type_ids[0].name + ' (' + \
                    letter.sponsorship_id.partner_id.ref + " - " + \
                    letter.child_id.local_id + ')'
            else:
                letter.name = _('New correspondence')

    @api.depends('sponsorship_id')
    def _set_partner_review(self):
        for letter in self:
            if letter.partner_id.mandatory_review:
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

    @api.multi
    def _inverse_original(self):
        self._set_text('original_text', self.original_text)

    @api.multi
    def _inverse_english(self):
        self._set_text('english_translated_text', self.english_text)

    @api.multi
    def _inverse_translated(self):
        self._set_text('translated_text', self.translated_text)

    @api.multi
    def _set_text(self, field, text):
        # Try to put text in correct pages (the text should contain
        # separators).
        if not text:
            return
        for letter in self:
            pages_text = text.split(PAGE_SEPARATOR)
            if letter.page_ids:
                if len(pages_text) <= len(letter.page_ids):
                    for i in range(0, len(pages_text)):
                        setattr(letter.page_ids[i], field,
                                pages_text[i].strip('\n'))
                else:
                    for i in range(0, len(letter.page_ids)):
                        setattr(letter.page_ids[i], field,
                                pages_text[i].strip('\n'))
                    last_page_text = getattr(letter.page_ids[i], field)
                    last_page_text += '\n\n' + '\n\n'.join(pages_text[i + 1:])
            else:
                for i in range(0, len(pages_text)):
                    letter.page_ids.create({
                        field: pages_text[i].strip('\n'),
                        'correspondence_id': letter.id})

    def _get_text(self, source_text):
        """ Gets the desired text (original/translated) from the pages. """
        txt = self.page_ids.filtered(source_text).mapped(source_text)
        return ('\n' + PAGE_SEPARATOR + '\n').join(txt)

    def _change_language(self):
        return True

    @api.multi
    @api.depends('letter_image')
    def _compute_letter_format(self):
        for letter in self.filtered('letter_image'):
            ftype = magic.from_buffer(base64.b64decode(
                letter.letter_image), True)
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
                match = re.search(r'(.*)\[(.*)\]', letter.translator)
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
    def _inverse_set_translator(self):
        """ Sets the translator e-mail address. """
        for letter in self:
            if letter.translator:
                match = re.search(r'(.*)\[(.*)\]', letter.translator)
                if match:
                    letter.translator_id.translator_email = match.group(2)

    def _get_uuid(self):
        return str(uuid.uuid4())

    def _compute_is_final_letter(self):
        for letter in self:
            letter.is_final_letter = \
                'Final Letter' in letter.communication_type_ids.mapped(
                    'name') or letter.sponsorship_state != 'active'

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

        type_ = '.pdf'
        letter_data = False
        if vals.get('letter_image'):
            letter_data = base64.b64decode(vals['letter_image'])
            ftype = magic.from_buffer(letter_data, True).lower()
            if 'pdf' in ftype:
                type_ = '.pdf'
            elif 'tiff' in ftype:
                type_ = '.tiff'
            else:
                raise UserError(
                    _('You can only attach tiff or pdf files'))
        letter = super(Correspondence, self).create(vals)
        letter.file_name = letter._get_file_name()
        if letter_data and type_ == '.pdf':
            # Set the correct number of pages
            image_pdf = PdfFileReader(BytesIO(letter_data))
            if letter.nbr_pages < image_pdf.numPages:
                for i in range(letter.nbr_pages, image_pdf.numPages):
                    letter.page_ids.create({'correspondence_id': letter.id})

        if not self.env.context.get('no_comm_kit'):
            letter.create_commkit()

        return letter

    @api.multi
    def write(self, vals):
        """ Keep track of state changes. """
        if 'state' in vals:
            vals['status_date'] = fields.Datetime.now()
        return super(Correspondence, self).write(vals)

    @api.multi
    def unlink(self):
        if not self.env.context.get('force_delete'):
            for letter in self:
                if letter.kit_identifier or \
                        letter.state == 'Global Partner translation queue':
                    raise UserError(
                        _("You cannot delete a letter which is in "
                          "translation or already sent to GMC."))
        # Remove unsent messages
        gmc_action = self.env.ref('sbc_compassion.create_letter')
        gmc_messages = self.env['gmc.message.pool'].search([
            ('action_id', '=', gmc_action.id),
            ('object_id', 'in', self.ids),
            ('state', 'in', ['new', 'failure', 'postponed'])
        ])
        gmc_messages.unlink()
        return super(Correspondence, self).unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def create_commkit(self):
        for letter in self:
            action_id = self.env.ref('sbc_compassion.create_letter').id
            message = self.env['gmc.message.pool'].create({
                'action_id': action_id,
                'object_id': letter.id,
                'child_id': letter.child_id.id,
                'partner_id': letter.partner_id.id
            })
            if letter.sponsorship_id.state not in ('active', 'terminated') or\
                    letter.child_id.project_id.hold_s2b_letters:
                message.state = 'postponed'
                if letter.child_id.project_id.hold_s2b_letters:
                    letter.state = 'Exception'
                    letter.message_post(
                        _('Letter was put on hold because the project is '
                          'suspended'), _('Project suspended'))
        return True

    @api.multi
    def compose_letter_button(self):
        """ Remove old images, download original and compose translation. """
        self.attach_original()
        return self.compose_letter_image()

    @api.multi
    def compose_letter_image(self):
        """
        Puts the translated text of a letter inside the original image given
        the child letter layout.
        :return: True if the composition succeeded, False otherwise
        """
        self.ensure_one()
        layout = self.b2s_layout_id
        image_data = base64.b64decode(self.letter_image)
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
        if self.partner_id.lang == 'de_DE':
            additional_pages_header = 'Seite '
        elif self.partner_id.lang == 'it_IT':
            additional_pages_header = 'Pagina '

        def get_chars(t):
            return "".join(re.findall("[a-zA-Z]+", t))

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
                        str(i + 1) + ':\n' + text
                else:
                    remaining_text = additional_pages_header + str(i + 1) +\
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
                        _('Translation went out of the translation box'),
                        _('Translation too long'))

                # Merge the translation on the existing page
                page = page_output.getPage(j)
                page.mergePage(translation_pdf.getPage(0))
                # Compress page
                page.compressContentStreams()
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
        self.letter_image = base64.b64encode(output_stream.read())

        return True

    @api.model
    def process_commkit(self, commkit_data):
        """ Update or Create the letter with given values. """
        self.process_lock.acquire()
        try:
            letter_mapping = mapping.new_onramp_mapping(self._name, self.env)
            letter_ids = list()
            process_letters = self
            for commkit in commkit_data.get('Responses', [commkit_data]):
                vals = letter_mapping.get_vals_from_connect(commkit)
                published_state = 'Published to Global Partner'
                is_published = vals.get('state') == published_state

                # Write/update letter
                kit_identifier = vals.get('kit_identifier')
                letter = self.search([('kit_identifier', '=', kit_identifier)])
                if letter:
                    # Avoid to publish twice a same letter
                    is_published = is_published and letter.state != \
                        published_state
                    if is_published or letter.state != published_state:
                        letter.write(vals)
                else:
                    if 'id' in vals:
                        del vals['id']
                    letter = self.with_context(no_comm_kit=True).create(vals)

                if is_published:
                    process_letters += letter

                letter_ids.append(letter.id)

            process_letters.process_letter()
        finally:
            self.process_lock.release()
        return letter_ids

    def on_send_to_connect(self):
        """
        Method called before Letter is sent to GMC.
        Upload the image to Persistence if not already done.
        """
        onramp = SBCConnector()
        for letter in self.filtered(lambda l: not l.original_letter_url):
            letter.original_letter_url = onramp.send_letter_image(
                letter.letter_image, letter.letter_format)

    @api.multi
    def enrich_letter(self, vals):
        """
        Enrich correspondence data with GMC data after CommKit Submission.
        Check that we received a valid kit identifier.
        """
        if vals.get('kit_identifier', 'null') == 'null':
            raise UserError(
                _('No valid kit id was returned. This is most '
                  'probably because the sponsorship is not known.'))
        return self.write(vals)

    def process_letter(self):
        """ Method called when new B2S letter is Published. """
        self.download_attach_letter_image(type='original_letter_url')
        res = True
        for letter in self:
            if letter.original_language_id not in \
                    letter.supporter_languages_ids:
                res = res and letter.compose_letter_image()
        return res

    @api.multi
    def download_attach_letter_image(self, type='final_letter_url'):
        """ Download letter image from US service and attach to letter. """
        for letter in self:
            # Download and store letter
            letter_url = getattr(letter, type)
            image_data = None
            if letter_url:
                image_data = SBCConnector().get_letter_image(
                    letter_url, 'pdf', dpi=300)  # resolution
            if image_data is None:
                raise UserError(
                    _("Image of letter {} was not found remotely.").format(
                        letter.kit_identifier))
            letter.write({
                'file_name': letter._get_file_name(),
                'letter_image': image_data
            })

    @api.multi
    def attach_original(self):
        self.download_attach_letter_image(type='original_letter_url')
        return True

    def get_image(self):
        """ Method for retrieving the image """
        self.ensure_one()
        data = base64.b64decode(self.letter_image)
        return data

    def hold_letters(self, message='Project suspended'):
        """ Prevents to send S2B letters to GMC. """
        self.write({
            'state': 'Exception'
        })
        for letter in self:
            letter.message_post(
                _('Letter was put on hold'), message)
        gmc_action = self.env.ref('sbc_compassion.create_letter')
        gmc_messages = self.env['gmc.message.pool'].search([
            ('action_id', '=', gmc_action.id),
            ('object_id', 'in', self.ids),
            ('state', 'in', ['new', 'failure'])
        ])
        gmc_messages.write({'state': 'postponed'})

    def reactivate_letters(self, message='Project reactivated'):
        """ Release the hold on S2B letters. """
        self.write({
            'state': 'Received in the system'
        })
        for letter in self:
            letter.message_post(
                _('The letter can now be sent.'), message)
        gmc_action = self.env.ref('sbc_compassion.create_letter')
        gmc_messages = self.env['gmc.message.pool'].search([
            ('action_id', '=', gmc_action.id),
            ('object_id', 'in', self.ids),
            ('state', '=', 'postponed')
        ])
        gmc_messages.write({'state': 'new'})

    @api.model
    def migrate_attachments(self):
        """ This method is specific for migration > 10.0.1.1.0
            so that the attachments can be correctly linked to the letters.
            It is not put inside a migration script because the method is
            very slow. Therefore we commit at each letter to avoid having to
            start all over again in case of failure.
        """
        attachment_obj = self.env['ir.attachment']
        _logger.info("Migration of correspondence attachments started !")
        letters = self.search([('letter_image', '=', False)], order='id desc')
        total = len(letters)
        index = 1
        for letter in letters:
            _logger.info("... moving attachment of letter {}/{}"
                         .format(index, total))
            attachments = attachment_obj.search([
                ('res_model', '=', 'correspondence'),
                ('res_id', '=', letter.id)
            ], order='id desc')
            if attachments:
                letter.write({
                    'letter_image': attachments[0].datas,
                    'file_name': attachments[0].name
                })
                attachments.unlink()
            if not test_mode:
                self.env.cr.commit()    # pylint: disable=invalid-commit
            index += 1
        return True

    @api.multi
    def _get_file_name(self):
        self.ensure_one()
        name = ''
        if self.communication_type_ids.ids:
            name = self.communication_type_ids[0].with_context(
                lang=self.partner_id.lang).name + ' '
        name += self.child_id.local_id
        if self.kit_identifier:
            name += ' ' + self.kit_identifier
        name += '.' + (self.letter_format or 'pdf')
        return name
