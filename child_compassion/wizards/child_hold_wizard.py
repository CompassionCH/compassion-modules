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
from ..models.compassion_hold import AbstractHold  # NOQA
from odoo import models, api, fields, _


class ChildHoldWizard(models.TransientModel):

    _name = 'child.hold.wizard'
    _inherit = 'compassion.abstract.hold'

    return_action = fields.Selection(
        'get_action_selection', required=True, default='view_children')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def get_action_selection(self):
        return [
            ('view_children', _('View Children')),
            ('view_holds', _('View Holds')),
            ('search', _('Search for other children')),
        ]

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def get_hold_values(self):
        hold_vals = super(ChildHoldWizard, self).get_hold_values()
        if self.channel in ('ambassador', 'event'):
            hold_vals['secondary_owner'] = self.ambassador.name
        return hold_vals

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

        return self._get_action(holds)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_action(self, holds):
        """ Returns the action after closing the wizard. """
        action = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': self.env.context,
            'target': 'current',
        }
        if self.return_action == 'view_children':
            action.update({
                'name': _('Children on hold'),
                'domain': [('id', 'in', holds.mapped('child_id').ids)],
                'res_model': 'compassion.child',
            })
        elif self.return_action == 'view_holds':
            action.update({
                'name': _('Created holds'),
                'domain': [('id', 'in', holds.ids)],
                'res_model': 'compassion.hold',
            })
        elif self.return_action == 'search':
            action = True

        return action
