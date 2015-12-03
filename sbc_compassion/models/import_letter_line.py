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


class ImportLetterLine(models.Model):
    """
    This class is used for the validation of an export.
    """

    _name = 'import.letter.line'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sponsorship_id = fields.Many2one('recurring.contract', 'Sponsorship',
                                     compute='_set_sponsorship_id')
    sponsorship_found = fields.Boolean(compute='_set_sponsorship_id')
    child_partner_found = fields.Boolean(compute='_set_sponsorship_id')
    partner_id = fields.Many2one('res.partner', 'Partner')
    name = fields.Char(compute='_set_name')
    child_id = fields.Many2one('compassion.child', 'Child')
    template_id = fields.Many2one(
        'sponsorship.correspondence.template', 'Template')
    supporter_languages_id = fields.Many2one(
        'res.lang.compassion', 'Language')
    is_encourager = fields.Boolean('Encourager', default=False)
    letter_image = fields.Many2one('ir.attachment')
    letter_image_preview = fields.Binary()
    import_id = fields.Many2one('import.letters.history')

    status = fields.Selection([
        ("no_lang", _("Language not Detected")),
        ("no_sponsorship", _("Sponsorship not Found")),
        ("no_child_partner", _("Partner or Child not Found")),
        ("no_template", _("Template not Detected")),
        ("ok", _("OK"))], compute="_check_status")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.multi
    @api.depends('partner_id', 'child_id', 'sponsorship_id',
                 'supporter_languages_id')
    def _check_status(self):
        """ At each change, check if all the fields are OK
        """
        default_template = self.env.ref('sbc_compassion.default_template')
        for line in self:
            if not line.sponsorship_found:
                line.status = "no_sponsorship"
                if not line.child_partner_found:
                    line.status = "no_child_partner"
            elif not line.template_id or (line.template_id.id ==
                                          default_template.id):
                line.status = "no_template"
            elif len(line.supporter_languages_id) != 1:
                line.status = "no_lang"
            else:
                line.status = "ok"

    @api.multi
    @api.depends('partner_id', 'child_id')
    def _set_sponsorship_id(self):
        """ From the partner codega and the child code, find the record
        linking them together.
        At the same time, check if the child, the partner and the sponsorship
        are found.
        """
        for line in self:
            if line.partner_id and line.child_id:
                line.sponsorship_id = line.env['recurring.contract'].search([
                    ('child_code', '=', line.child_id.code),
                    ('partner_codega', '=', line.partner_id.ref)],
                    order='is_active desc, end_date desc', limit=1)
                if line.sponsorship_id:
                    line.sponsorship_found = True
                    line.child_partner_found = True
                else:
                    line.sponsorship_found = False
                    if not (line.env['recurring.contract'].search([
                            ('child_code', '=', line.child_id.code)]) and
                            line.env['recurring.contract'].search([
                                ('partner_codega', '=',
                                 line.partner_id.ref)])):
                        line.child_partner_found = False
                    else:
                        line.child_partner_found = True

    @api.multi
    @api.depends('partner_id', 'child_id')
    def _set_name(self):
        for line in self:
            if line.sponsorship_id:
                line.name = str(
                    line.sponsorship_id.partner_codega) + " - " + str(
                        line.child_id.code)

    @api.multi
    def get_letter_data(self, mandatory_review=False):
        """ Create a list of dictionaries in order to create some lines inside
        import_letters_history.

        :param mandatory_review: Are all the lines mandatory review?
        :returns: list to use in a write
        :rtype: list[dict{}]

        """
        letter_data = []
        for line in self:
            vals = {
                'sponsorship_id': line.sponsorship_id.id,
                'letter_image': line.letter_image.datas,
                'template_id': line.template_id.id,
                'original_language_id': line.supporter_languages_id.id,
                'direction': 'Supporter To Beneficiary'
            }
            if line.is_encourager:
                vals['relationship'] = 'Encourager'
            if mandatory_review:
                vals['mandatory_review'] = True
            letter_data.append((0, 0, vals))
        return letter_data
