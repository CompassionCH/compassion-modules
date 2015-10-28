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


class ImportLetterLine(models.TransientModel):

    """ This class is used for the validation of an exportation.
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
        """
        default_template = self.env.ref('sbc_compassion.default_template')
        for inst in self:
            if inst.sponsorship_status or inst.is_encourager:
                inst.status = "encourager"
            if inst.sponsorship_status is True:
                inst.status = "sponsor"
            elif not inst.template_id or (inst.template_id.id ==
                                          default_template.id):
                inst.status = "temp"
            elif len(inst.supporter_languages_id) != 1:
                inst.status = "lang"
            else:
                inst.status = "ok"

    @api.multi
    @api.depends('partner_codega', 'child_code')
    def _set_sponsorship_id(self):
        for inst in self:
            if inst.partner_codega and inst.child_code:
                test = (inst.env['recurring.contract'].search(
                    [('child_id.code', '=', inst.child_code)]) and
                    inst.env['recurring.contract'].search([
                        ('partner_codega', '=', inst.partner_codega)]))

                inst.sponsorship_id = inst.env['recurring.contract'].search([
                    ('child_id.code', '=', inst.child_code),
                    ('partner_codega', '=', inst.partner_codega)])
                if len(inst.sponsorship_id) == 1:
                    inst.sponsorship_status = None
                elif test:
                    inst.sponsorship_status = True
                else:
                    inst.sponsorship_status = False

    @api.multi
    @api.depends('partner_codega', 'child_code')
    def _set_name(self):
        for inst in self:
            if inst.sponsorship_id:
                inst.name = str(
                    inst.sponsorship_id.partner_codega) + " - " + str(
                        inst.child_code)
