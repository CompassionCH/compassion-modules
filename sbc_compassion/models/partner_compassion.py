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

from openerp import fields, models, api


class ResPartner(models.Model):
    """ Add correspondence preferences to Partners
    """
    _inherit = 'res.partner'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    spoken_lang_ids = fields.Many2many(
        'res.lang.compassion', string='Spoken languages')
    letter_delivery_preference = fields.Selection(
        selection='_get_delivery_preference',
        default='auto_digital',
        required=True,
        help='Delivery preference for Child Letters',
        oldname='delivery_preference')
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
