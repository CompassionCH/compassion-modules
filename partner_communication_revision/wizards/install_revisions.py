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
from odoo import models, api


class RevisionInstall(models.AbstractModel):
    _name = 'partner.communication.revision.install'

    @api.model
    def install(self):
        configs = self.env['partner.communication.config'].search([])
        revision_obj = self.env['partner.communication.revision']
        langs = set(self.env['res.lang'].search([]))
        for config in configs:
            revision_langs = set(config.revision_ids.mapped('lang'))
            langs_missing = (lang for lang in langs \
                             if lang.code not in revision_langs)
            revision_date = config.email_template_id.write_date
            for lang in langs_missing:
                revision_obj.create({
                    'lang': lang.code,
                    'config_id': config.id,
                    'revision_date': revision_date
                })
            config.revision_date = revision_date
        return True
