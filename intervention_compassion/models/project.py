# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class FCP(models.Model):
    _inherit = 'compassion.project'

    intervention_ids = fields.Many2many(
        'compassion.intervention', 'fcp_interventions',
        'fcp_id', 'intervention_id', 'Interventions'
    )
    nb_interventions = fields.Integer(compute='_compute_nb_interventions')

    @api.multi
    def _compute_nb_interventions(self):
        for project in self:
            project.nb_interventions = len(project.intervention_ids)

    @api.multi
    def open_interventions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Interventions',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'compassion.intervention',
            'res_id': self.intervention_ids.ids,
            'domain': [('id', 'in', self.intervention_ids.ids)],
            'target': 'current',
            'context': self.env.context
        }
