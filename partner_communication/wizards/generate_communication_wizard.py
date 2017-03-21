# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import models, api, fields, _


class GenerateCommunicationWizard(models.TransientModel):
    _name = 'partner.communication.generate.wizard'

    partner_ids = fields.Many2many('res.partner', string='Recipients')
    model_id = fields.Many2one(
        'partner.communication.config', 'Template',
        domain=[('model', '=', 'res.partner')]
    )

    @api.multi
    def generate(self):
        comm_obj = self.env['partner.communication.job']
        comm = comm_obj
        for partner in self.partner_ids:
            comm += comm_obj.create({
                'partner_id': partner.id,
                'object_ids': partner.id,
                'config_id': self.model_id.id,
                'auto_send': False,
            })

        return {
            'name': _('Communications'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': comm_obj._name,
            'context': self.env.context,
            'domain': [('id', 'in', comm.ids)]
        }
