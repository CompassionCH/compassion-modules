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
from odoo import api, models, fields


class CommunicationConfig(models.Model):
    _inherit = 'partner.communication.config'

    revision_number = fields.Float(default=1.0, readonly=True)
    revision_date = fields.Date(default=fields.Date.today(), readonly=True)
    revision_ids = fields.One2many(
        'partner.communication.revision', 'config_id', 'Revisions'
    )

    @api.multi
    def new_proposition(self):
        """
        Called for creating a new revision text
        :return: view action for editing proposition text
        """
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'res_model': self._name,
            'target': 'current',
            'context': self.env.context
        }
