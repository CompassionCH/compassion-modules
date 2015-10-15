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
import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../tools'))
from positionpattern import Layout

class ImportMailLine(models.TransientModel):

    """ This class is used for the validation of an exportation.
    """

    _name = 'import.mail.line'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sponsorship_id = fields.Many2one('recurring.contract', 'Sponsorship',
                                     compute='_set_sponsorship_id')
    sponsorship_status = fields.Boolean(compute='_set_sponsorship_id',
                                        readonly=True)
    partner_codega = fields.Char(string=_("Partner"))
    name = fields.Char(compute='_set_name')
    child_code = fields.Char(string=_("Child"))
    template_id = fields.Selection([
        (Layout.name[0], _('Template 1')),
        (Layout.name[1], _('Template 2')),
        (Layout.name[2], _('Template 3')),
        (Layout.name[3], _('Template 4')),
        (Layout.name[4], _('Template 5')),
        (Layout.name[5], _('Template 6'))], string=_("Template"))
    supporter_languages_id = fields.Many2one(
        'res.lang.compassion',string="Language")
    is_encourager = fields.Boolean(string=_("Encourager"))
    letter_image = fields.Many2one('ir.attachment')
    letter_image_preview = fields.Binary()
    # a little bit complicated due to if, elif,... in _check_status
    # True -> error in sponsorship_id
    # None -> one id is found (Perfect case)
    # False -> error in partner or child
    status = fields.Char(compute="_check_status")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    
    @api.depends('partner_codega','child_code','sponsorship_id',
                 'supporter_languages_id')
    def _check_status(self):
        """
        """
        # == avoid problems with None
        if self.sponsorship_status == True and not self.is_encourager.read():
            self.status = _('Sponsorship not found')
        if not self.sponsorship_status == False:
            self.status = _('Error in Sponsorship')
        elif self.template_id not in Layout.name: 
            self.status = _('Error in Template')
        elif len(self.supporter_languages_id) != 1:
            self.status = _('Error in Language')
        else:
            self.supporter_languages_id.ensure_one()
            self.status = _('OK')

    @api.depends('partner_codega', 'child_code')
    def _set_sponsorship_id(self):
        if self.partner_codega and self.child_code:
            test = (self.env['recurring.contract'].search([
                ('child_id.code','=',self.child_code)]) and
                    self.env['recurring.contract'].search([
                        ('partner_codega','=',self.partner_codega)]))

            self.sponsorship_id = self.env['recurring.contract'].search([
                ('child_id.code', '=', self.child_code),
                ('partner_codega', '=', self.partner_codega)])
            if len(self.sponsorship_id) == 1:
                self.sponsorship_status = None
            elif test:
                self.sponsorship_status = True
            else:
                self.sponsorship_status = False
                

    @api.depends('partner_codega','child_code')
    def _set_name(self):
        if self.sponsorship_id:
            self.name = str(
                self.sponsorship_id.partner_codega) + " - " + str(
                    self.child_code)
