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
from openerp import models, api, fields, _


class ChildHoldWizard(models.TransientModel):

    _name = 'child.hold.wizard'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    name = fields.Char()
    type = fields.Selection(selection=[
        ('Available', _('Available')),
        ('Change Commitment Hold', _('Change Commitment Hold')),
        ('Consignment Hold', _('Consignment Hold')),
        ('Delinquent Mass Cancel Hold', _('Delinquent Mass Cancel Hold')),
        ('E-Commerce Hold', _('E-Commerce Hold')),
        ('Inactive', _('Inactive')),
        ('Ineligible', _('Ineligible')),
        ('No Money Hold', _('No Money Hold')),
        ('Reinstatement Hold', _('Reinstatement Hold')),
        ('Reservation Hold', _('Reservation Hold')),
        ('Sponsor Cancel Hold', _('Sponsor Cancel Hold')),
        ('Sponsored', _('Sponsored')),
        ('Sub Child Hold', _('Sub Child Hold'))], required=True)
    hold_expiration_date = fields.Datetime(required=True)
    primary_owner = fields.Char(required=True,
                                default=lambda self: self.env.user.name)
    secondary_owner = fields.Char()
    no_money_yield_rate = fields.Float()
    yield_rate = fields.Float()
    channel = fields.Selection([
        ('web', _('Website')),
        ('event', _('Event')),
        ('ambassador', _('Ambassador')),
    ])
    source_code = fields.Char('Source')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.multi
    def create_hold_vals(self, child_comp):
        return {
            'name': self.name,
            'child_id': child_comp.id,
            'type': self.type,
            'expiration_date': self.hold_expiration_date,
            'primary_owner': self.primary_owner,
            'secondary_owner': self.secondary_owner,
            'no_money_yield_rate': self.no_money_yield_rate,
            'yield_rate': self.yield_rate,
            'channel': self.channel,
            'source_code': self.source_code,
        }

    @api.multi
    def create_child_vals(self, child):
        return {
            'global_id': child.global_id,
            'local_id': child.local_id,
            'project_id': child.project_id.id,
            'field_office_id': child.field_office_id,
            'name': child.name,
            'firstname': child.firstname,
            'lastname': child.lastname,
            'preferred_name': child.preferred_name,
            'gender': child.gender,
            'birthdate': child.birthdate,
            'age': child.age,
            'is_orphan': child.is_orphan,
            'beneficiary_state ': child.beneficiary_state,
            'sponsorship_status': child.sponsorship_status,
            'unsponsored_since': child.unsponsored_since,
        }

    @api.multi
    def send(self):

        holds = self.env['compassion.hold']
        messages = self.env['gmc.message.pool']
        child_search = self.env['compassion.childpool.search'].browse(
            self.env.context.get('active_id')).global_child_ids

        for child in child_search:
            # Save children form global children to compassion children

            child_vals = self.create_child_vals(child)
            child_comp = self.env['compassion.child'].create(child_vals)

            # Create Holds for children to reserve
            hold_vals = self.create_hold_vals(child_comp)
            hold = holds.create(hold_vals)
            holds += hold

            # create messages to send to Connect
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
