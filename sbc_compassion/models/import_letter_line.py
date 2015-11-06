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
    This class is used for the validation of an exportation.
    """

    _name = 'import.letter.line'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sponsorship_id = fields.Many2one('recurring.contract', 'Sponsorship',
                                     compute='_set_sponsorship_id')
    sponsorship_status = fields.Boolean(compute='_set_sponsorship_id',
                                        readonly=True)
    partner_codega = fields.Char('Partner')
    name = fields.Char(compute='_set_name')
    child_code = fields.Char('Child')
    template_id = fields.Many2one(
        'sponsorship.correspondence.template', 'Template')
    supporter_languages_id = fields.Many2one(
        'res.lang.compassion', 'Language')
    is_encourager = fields.Boolean('Encourager', default=False)
    letter_image = fields.Many2one('ir.attachment')
    letter_image_preview = fields.Binary()

    status = fields.Selection([
        ("lang", _("Error in Language")),
        ("sponsor", _("Error in Sponsorship")),
        ("encourager", _("Sponsorship not found")),
        ("temp", _("Error in Template")),
        ("ok", _("OK"))], compute="_check_status")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.multi
    @api.depends('partner_codega', 'child_code', 'sponsorship_id',
                 'supporter_languages_id')
    def _check_status(self):
        """
        At each change, check if all the fields are OK
        """
        default_template = self.env.ref('sbc_compassion.default_template')
        for line in self:
            if line.sponsorship_status or line.is_encourager:
                line.status = "encourager"
            if line.sponsorship_status is True:
                line.status = "sponsor"
            elif not line.template_id or (line.template_id.id ==
                                          default_template.id):
                line.status = "temp"
            elif len(line.supporter_languages_id) != 1:
                line.status = "lang"
            else:
                line.status = "ok"

    @api.multi
    @api.depends('partner_codega', 'child_code')
    def _set_sponsorship_id(self):
        for line in self:
            if line.partner_codega and line.child_code:
                line.sponsorship_id = line.env['recurring.contract'].search([
                    ('child_id.code', '=', line.child_code),
                    ('partner_codega', '=', line.partner_codega),
                    ('is_active', '=', True)], order='end_date desc', limit=1)
                if len(line.sponsorship_id) == 1:
                    line.sponsorship_status = None
                else:
                    line.sponsorship_status = False

    @api.multi
    @api.depends('partner_codega', 'child_code')
    def _set_name(self):
        for line in self:
            if line.sponsorship_id:
                line.name = str(
                    line.sponsorship_id.partner_codega) + " - " + str(
                        line.child_code)
