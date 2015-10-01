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

from openerp import fields, models, api


class ImportMailLine(models.TransientModel):

    """ This class is used for the validation of an exportation.
    """

    _name = 'import.mail.line'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sponsorship_id = fields.Many2one('recurring.contract', 'Sponsorship',
                                     required=True,
                                     compute='_set_sponsorship_id')
    partner_codega = fields.Char()
    name = fields.Char(compute='_set_name')
    child_code = fields.Char()
    template_id = template_id = fields.Selection([
        ('template_1', 'Template 1'),
        ('template_2', 'Template 2'),
        ('template_3', 'Template 3'),
        ('template_4', 'Template 4'),
        ('template_5', 'Template 5')], required=True)
    supporter_languages_id = fields.Many2one(
        'res.lang.compassion')
    is_encourager = fields.Boolean()
    letter_image = fields.Many2one('ir.attachment')
    letter_image_preview = fields.Many2one('ir.attachment')
    status = fields.Selection([
        ('ok', 'Ok'),
        ('need_modifications', 'Need modifications'),
        ('failure', 'Failure')])

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.depends('partner_codega', 'child_code')
    def _set_sponsorship_id(self):
        if self.partner_codega and self.child_code:
            self.sponsorship_id = self.env['recurring.contract'].search([
                ('child_id.code', '=', self.child_code),
                ('partner_codega', '=', self.partner_codega)])

    @api.depends('partner_codega')
    def _set_name(self):
        if self.sponsorship_id:
            self.name = str(
                self.sponsorship_id.partner_codega) + " - " + str(
                    self.child_code)
