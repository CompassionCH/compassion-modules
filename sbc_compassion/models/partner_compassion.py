# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models, api


class ResPartner(models.Model):
    """ Add correspondence preferences to Partners
    """
    _inherit = 'res.partner'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    spoken_lang_ids = fields.Many2many(
        'res.lang.compassion', string='Spoken languages',
        groups='child_compassion.group_sponsorship'
    )
    translator_email = fields.Char(
        help='e-mail address used in SDL',
        groups='child_compassion.group_sponsorship'
    )
    nb_letters = fields.Integer(
        compute='_compute_nb_letters',
        groups='child_compassion.group_sponsorship'
    )
    translated_letter_ids = fields.One2many(
        'correspondence', 'translator_id', 'Translated letters')

    @api.multi
    def _compute_nb_letters(self):
        for partner in self:
            partner.nb_letters = self.env['correspondence'].search_count([
                ('partner_id', '=', partner.id)
            ])

    @api.model
    def create(self, vals):
        if 'spoken_lang_ids' not in vals:
            lang_ids = self.env['res.lang.compassion'].search([
                ('lang_id.code', '=', vals.get('lang', self.env.lang))
            ]).ids
            vals['spoken_lang_ids'] = [(6, 0, lang_ids)]
        return super(ResPartner, self).create(vals)

    @api.multi
    def open_letters(self):
        """ Open the tree view correspondence of partner """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Letters',
            'res_model': 'correspondence',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': self.with_context(
                group_by=False,
                search_default_partner_id=self.id
            ).env.context,
        }

    @api.onchange('lang')
    def onchange_main_language(self):
        lang = self.env['res.lang'].search([('code', '=', self.lang)])
        spoken_lang = self.env['res.lang.compassion'].search([
            ('lang_id', '=', lang.id)])
        if spoken_lang:
            self.spoken_lang_ids += spoken_lang

    @api.multi
    def forget_me(self):
        super(ResPartner, self).forget_me()
        # Delete correspondence
        self.env['correspondence'].with_context(force_delete=True).search([
            ('partner_id', '=', self.id)]).unlink()
        return True
