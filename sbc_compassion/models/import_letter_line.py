# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models, api, _


class ImportLetterLine(models.Model):
    """
    This class is used for the validation of an export.
    """

    _name = 'import.letter.line'
    _inherit = 'import.letter.config'
    _order = 'reviewed,status'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sponsorship_id = fields.Many2one('recurring.contract', 'Sponsorship',
                                     compute='_compute_sponsorship')
    partner_id = fields.Many2one('res.partner', 'Partner')
    name = fields.Char(compute='_compute_name')
    child_id = fields.Many2one('compassion.child', 'Child')
    letter_language_id = fields.Many2one(
        'res.lang.compassion', 'Language')
    letter_image = fields.Binary(attachment=True, readonly=True)
    file_name = fields.Char(readonly=True)
    letter_image_preview = fields.Binary(attachment=True, readonly=True)
    import_id = fields.Many2one('import.letters.history')
    reviewed = fields.Boolean()
    status = fields.Selection([
        ("no_lang", _("Language not Detected")),
        ("no_sponsorship", _("Sponsorship not Found")),
        ("no_child_partner", _("Partner or Child not Found")),
        ("no_template", _("Template not Detected")),
        ("ok", _("OK"))], compute="_compute_check_status",
        store=True, readonly=True)
    original_text = fields.Text()
    original_attachment_ids = fields.One2many('ir.attachment', 'res_id',
                                              domain=[('res_model', '=', _name)],
                                              readonly=True,
                                              ondelete='cascade',
                                              string="Attached images")

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        # Fetch default values in import configuration.
        create_vals = dict()
        if vals.get('import_id'):
            config = self.env['import.letters.history'].browse(
                vals['import_id'])
            create_vals = config.get_correspondence_metadata()
        create_vals.update(vals)
        return super(ImportLetterLine, self).create(create_vals)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.multi
    @api.depends('partner_id', 'child_id', 'sponsorship_id',
                 'letter_language_id', 'import_id.template_id')
    def _compute_check_status(self):
        """ At each change, check if all the fields are OK
        """
        default_template = self.env.ref('sbc_compassion.default_template')
        for line in self:
            valid_template = (
                line.template_id and not
                (line.template_id == default_template !=
                 line.import_id.template_id))
            if not line.sponsorship_id:
                if not (line.child_id and line.partner_id):
                    line.status = "no_child_partner"
                else:
                    line.status = "no_sponsorship"
            elif not valid_template:
                line.status = "no_template"
            elif len(line.letter_language_id) != 1:
                line.status = "no_lang"
            else:
                line.status = "ok"

    @api.multi
    @api.depends('partner_id', 'child_id')
    def _compute_sponsorship(self):
        """ From the partner codega and the child code, find the record
        linking them together.
        At the same time, check if the child, the partner and the sponsorship
        are found.
        """
        for line in self:
            if line.partner_id and line.child_id:
                line.sponsorship_id = line.env['recurring.contract'].search([
                    ('child_id', '=', line.child_id.id),
                    ('correspondent_id', '=', line.partner_id.id)],
                    order='is_active desc, end_date desc', limit=1)

    @api.multi
    @api.depends('partner_id', 'child_id')
    def _compute_name(self):
        for line in self:
            if line.sponsorship_id:
                line.name = str(
                    line.sponsorship_id.partner_id.ref) + " - " + str(
                        line.child_id.local_id)

    @api.multi
    def get_letter_data(self):
        """ Create a list of dictionaries in order to create some lines inside
        import_letters_history.

        :returns: list to use in a write
        :rtype: list[dict{}]

        """
        letter_data = []
        for line in self:
            vals = line.get_correspondence_metadata()
            vals.update({
                'sponsorship_id': line.sponsorship_id.id,
                'letter_image': line.letter_image,
                'original_language_id': line.letter_language_id.id,
                'direction': 'Supporter To Beneficiary',
                'original_text': line.original_text,
                'source': line.source,
                'import_id': line.import_id.id,
            })
            if line.is_encourager:
                vals['relationship'] = 'Encourager'
            del vals['is_encourager']

            if line.source == 'website':
                # To save disk space, we prefer storing the text, images and template_id
                # rather than the PDF (which contains a large background).
                del vals['letter_image']
                vals['store_letter_image'] = False
                if line.original_attachment_ids:
                    vals['original_attachment_ids'] = line.original_attachment_ids

            letter_data.append(vals)
        return letter_data
