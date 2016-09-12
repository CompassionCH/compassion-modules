# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Philippe Heer
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from ..models.compassion_hold import AbstractHold   # nopep8
from openerp import models, api, _


class ChildHoldWizard(models.TransientModel):

    _name = 'child.hold.wizard'
    _inherit = 'compassion.abstract.hold'

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def send(self):

        holds = self.env['compassion.hold']
        messages = self.env['gmc.message.pool']
        child_search = self.env['compassion.childpool.search'].browse(
            self.env.context.get('active_id')).global_child_ids

        for child in child_search:
            # Save children form global children to compassion children
            child_comp = self.env['compassion.child'].create(
                child.get_child_vals())

            # Create Holds for children to reserve
            hold_vals = self.get_hold_values()
            hold_vals['child_id'] = child_comp.id
            hold = holds.create(hold_vals)
            holds += hold

            # Create messages to send to Connect
            action_id = self.env.ref('child_compassion.create_hold').id

            messages += messages.create({
                'action_id': action_id,
                'object_id': hold.id
            })
        messages.process_messages()

        return {
            'name': _('Created holds'),
            'domain': [('id', 'in', holds.ids)],
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'compassion.hold',
            'target': 'current',
        }
