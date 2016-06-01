# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import fields, models, api, _


class ResPartner(models.Model):
    """ Add correspondence preferences to Partners
    """

    _inherit = 'res.partner'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    spoken_lang_ids = fields.Many2many(
        'res.lang.compassion', string='Spoken languages')
    delivery_preference = fields.Selection([
        ('digital', _('By e-mail')),
        ('physical', _('By postal service'))], default='digital',
        required=True, help='Delivery preference for Child letters')
    translator_email = fields.Char(help='e-mail address used in SDL')

    @api.multi
    def open_letters(self):
        """ Open the tree view correspondence of partner """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Letters',
            'res_model': 'correspondence',
            "views": [[False, "tree"], [False, "form"]],
            'domain': [["correspondant_id", "=", self.id]],
            }

    @api.onchange('lang')
    def onchange_main_language(self):
        lang = self.env['res.lang'].search([('code', '=', self.lang)])
        spoken_lang = self.env['res.lang.compassion'].search([
            ('lang_id', '=', lang.id)])
        if spoken_lang:
            self.spoken_lang_ids += spoken_lang
