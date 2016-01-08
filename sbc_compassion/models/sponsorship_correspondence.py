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
    kit_identifier = fields.Char('Kit id', copy=False, readonly=True)
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
    state = fields.Selection('get_states', default='Received in the system')
    s2b_state = fields.Selection('get_s2b_states', compute='_compute_states')
    b2s_state = fields.Selection('get_b2s_states', compute='_compute_states')

    # 2. Attachments and scans
    ##########################
    letter_image = fields.Many2one('ir.attachment')
    letter_format = fields.Selection([
        ('pdf', 'pdf'), ('tiff', 'tiff')],
        compute='_compute_letter_format')
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
        'res.lang.compassion')
    destination_language_id = fields.Many2one(
        'res.lang.compassion', compute='_set_destination_language',
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
    mandatory_review = fields.Boolean()
    is_first_letter = fields.Boolean(
        compute='_compute_is_first',
        store=True,
        readonly=True)
    marked_for_rework = fields.Boolean()
    rework_reason = fields.Char()
    rework_comments = fields.Text()
    original_letter_url = fields.Char()
    final_letter_url = fields.Char()
    import_id = fields.Many2one('import.letters.history')

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
                if count == 0:
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

    @api.depends('sponsorship_id', 'direction', 'original_language_id')
    def _set_destination_language(self):
        for letter in self:
            if letter.direction == 'Supporter To Beneficiary':
                if letter.child_id.project_id.country_id.spoken_langs_ids:
                    if letter.original_language_id in letter.child_id.\
                       project_id.country_id.spoken_langs_ids:
                        letter.destination_language_id = letter.\
                            original_language_id
                    else:
                        letter.destination_language_id = letter\
                            .child_id.project_id.country_id.spoken_langs_ids[0]

            if letter.direction == 'Beneficiary To Supporter':
                if letter.child_id.project_id.country_id.spoken_langs_ids:
                    if letter.original_language_id in letter.\
                       correspondant_id.spoken_langs_ids:
                        letter.destination_language_id = letter.\
                            original_language_id
                    else:
                        letter.destination_language_id = letter\
                              .correspondant_id.spoken_langs_ids[0]

    @api.depends('sponsorship_id')
    def _set_partner_review(self):
        for letter in self:
            if letter.correspondant_id.mandatory_review:
                letter.mandatory_review = True

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
            ftype = magic.from_buffer(base64.b64decode(letter_image),
                                      True).lower()
            if 'pdf' in ftype:
                type_ = '.pdf'
            elif 'tiff' in ftype:
                type_ = '.tiff'
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
                'name': letter.scanned_date + '_' + letter.name + type_,
                'datas_fname': letter.name,
                'res_id': letter.id})
        return letter

    @api.multi
    def write(self, vals):
        """ Keep track of state changes. """
        if 'state' in vals:
            vals['status_date'] = fields.Date.today()
        return super(SponsorshipCorrespondence, self).write(vals)
