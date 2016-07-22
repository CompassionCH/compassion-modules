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
        ('Sub Child Hold', _('Sub Child Hold'))])
    hold_expiration_date = fields.Datetime()
    primary_owner = fields.Char()
    secondary_owner = fields.Char()
    no_money_yield_rate = fields.Float()
    yield_rate = fields.Float()
    channel = fields.Char()

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
            'source_code': '',
        }

    @api.multi
    def send(self):

        holds = self.env['compassion.hold']
        messages = self.env['gmc.message.pool']
        child_search = self.env['compassion.childpool.search'].browse(
            self.env.context.get('active_id')).global_child_ids

        for child in child_search:
            # Save children form global children to compassion children

            child_vals = {
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
        messages.with_context(async_mode=False).process_messages()

        # update compassion children with hold_id received
        for hold in holds:
            child_to_update = hold.child_id
            if hold.hold_id:
                child_vals = {
                    'hold_id': hold.id,
                    'active': True,
                    'state': 'N',
                }
                child_to_update.write(child_vals)
            else:
                # delete child if no hold_id received
                child_to_update.unlink()
                hold.unlink()

        return {
            'name': _('Created holds'),
            'domain': [('id', 'in', holds.ids)],
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'compassion.hold',
            'target': 'current',
        }
