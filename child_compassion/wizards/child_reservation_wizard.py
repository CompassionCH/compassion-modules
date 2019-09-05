##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, _


class ChildReservationWizard(models.TransientModel):
    _name = 'child.reservation.wizard'
    _inherit = 'compassion.abstract.hold'

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def get_hold_values(self):
        hold_vals = super().get_hold_values()
        if self.channel in ('ambassador', 'event'):
            hold_vals['secondary_owner'] = self.ambassador.name
        return hold_vals

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def send(self):
        reservation_obj = self.env['compassion.reservation']
        reservations = reservation_obj
        child_search = self.env['compassion.childpool.search'].browse(
            self.env.context.get('active_id')).global_child_ids

        for child in child_search:
            # Save children form global children to compassion children
            child_comp = self.env['compassion.child'].create(
                child.get_child_vals())
            reservation_vals = {
                'reservation_type': 'child',
                'state': 'draft',
                'child_id': child_comp.id,
                'reservation_expiration_date': self.expiration_date,
            }
            reservation_vals.update(self.get_hold_values())
            reservations += reservation_obj.create(reservation_vals)

        reservations.handle_reservation()

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': self.env.context,
            'name': _("Reservations"),
            'res_model': 'compassion.reservation',
            'domain': [('id', 'in', reservations.ids)],
            'target': 'current',
        }
