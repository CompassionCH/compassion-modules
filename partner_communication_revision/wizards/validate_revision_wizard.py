# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields


class ValidateRevisionWizard(models.TransientModel):
    _name = 'partner.communication.validate.proposition'
    _description = 'Validate proposition wizard'

    set_current_translation = fields.Integer(default=1)
    translation_revision_id = fields.Many2one(
        'partner.communication.revision',
        default=lambda s: s._default_revision())
    translator_user_id = fields.Many2one(
        'res.users', 'Translator',
        domain=[('share', '=', False)],
    )
    lang = fields.Selection(
        'select_lang', 'Lang of translation',
        related='translation_revision_id.lang', readonly=True)

    @api.model
    def select_lang(self):
        langs = self.env['res.lang'].search([])
        return [(lang.code, lang.name) for lang in langs]

    @api.model
    def _default_revision(self):
        revision = self.env['partner.communication.revision'].browse(
            self._context['active_id'])
        other_lang = revision.config_id.revision_ids - revision
        return other_lang[0]

    @api.multi
    def set_translator(self):
        revision = self.env['partner.communication.revision'].browse(
            self._context['active_id'])
        other_lang = revision.config_id.revision_ids - revision
        revision_lang = self.translation_revision_id
        if not revision_lang:
            revision.approve()
            return True

        revision_lang.write({
            'user_id': self.translator_user_id.id,
            'compare_lang': revision.lang,
            'compare_text': revision.proposition_text,
            'compare_subject': revision.subject,
        })
        if len(other_lang) > self.set_current_translation:
            self.write({
                'set_current_translation': self.set_current_translation + 1,
                'translation_revision_id': other_lang[
                    self.set_current_translation].id,
                'translator_user_id': False
            })
            return self._reload()
        revision.approve()
        return True

    def _reload(self):
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
