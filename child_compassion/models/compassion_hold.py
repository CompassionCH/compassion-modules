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

from openerp import api, models, fields, _
from openerp.exceptions import Warning

from ..mappings.childpool_create_hold_mapping import ReservationToHoldMapping


class CompassionHold(models.Model):
    _name = 'compassion.hold'

    name = fields.Char('Name')
    hold_id = fields.Char(readonly=True)
    child_id = fields.Many2one('compassion.child', 'Child on hold',
                               readonly=True)
    child_name = fields.Char(
        'Child on hold', related='child_id.name', readonly=True)
    type = fields.Selection([
        ('Available', 'Available'),
        ('Change Commitment Hold', 'Change Commitment Hold'),
        ('Consignment Hold', 'Consignment Hold'),
        ('Delinquent Mass Cancel Hold', 'Delinquent Mass Cancel Hold'),
        ('E-Commerce Hold', 'E-Commerce Hold'),
        ('Inactive', 'Inactive'),
        ('Ineligible', 'Ineligible'),
        ('No Money Hold', 'No Money Hold'),
        ('Reinstatement Hold', 'Reinstatement Hold'),
        ('Reservation Hold', 'Reservation Hold'),
        ('Sponsor Cancel Hold', 'Sponsor Cancel Hold'),
        ('Sponsored', 'Sponsored'),
        ('Sub Child Hold', 'Sub Child Hold')
    ])
    expiration_date = fields.Datetime()
    primary_owner = fields.Char()
    secondary_owner = fields.Char()
    no_money_yield_rate = fields.Float()
    yield_rate = fields.Float()
    channel = fields.Char()
    source_code = fields.Char()
    active = fields.Boolean(default=True, readonly=True)
    reservation_id = fields.Many2one('icp.reservation', 'Reservation')

    @api.multi
    def release_hold(self):
        message_obj = self.env['gmc.message.pool']
        action_id = self.env.ref('child_compassion.release_hold').id

        self.active = False
        message_vals = {
            'action_id': action_id,
            'object_id': self.id
        }

        if self.child_id.sponsor_id:
            raise Warning(_("Cancel impossible"), _("This hold is on a "
                                                    "sponsored child!"))
        else:
            self.child_id.active = False
            message_obj.create(message_vals)

    @api.model
    def check_hold_validity(self):
        expired_holds = self.env['compassion.hold'].search([
            ('expiration_date', '<',
             fields.Datetime.now())
        ])

        for expired_hold in expired_holds:
            expired_hold.child_id.active = False
            expired_hold.active = False

        return True

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        res = super(CompassionHold, self).write(vals)
        notify_vals = ['name', 'primary_owner', 'type', 'mandatory_review',
                       'expiration_date']
        notify = reduce(lambda prev, val: prev or val in vals, notify_vals,
                        False)
        if notify and not self.env.context.get('no_upsert'):
            self.update_hold()

        return res

    @api.multi
    def unlink(self):
        self.release_hold()
        return

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def update_hold(self):
        message_obj = self.env['gmc.message.pool']
        action_id = self.env.ref('child_compassion.create_hold').id

        message_vals = {
            'action_id': action_id,
            'object_id': self.id
        }
        message_obj.create(message_vals)

    @api.multi
    def hold_sent(self, vals):
        """ Called when hold is sent to Connect. """
        self.write(vals)
        # update compassion children with hold_id received
        for hold in self:
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

    @api.model
    def reservation_to_hold(self, commkit_data):
        """ Called when a reservation gots converted to a hold. """
        mapping = ReservationToHoldMapping(self.env)
        hold_data = commkit_data.get(
            'GlobalPartnerBeneficiaryReservationToHoldNotification')
        child_global_id = hold_data and hold_data.get('Beneficiary_GlobalID')
        if child_global_id:
            child = self.env['compassion.child'].create(
                {'global_id': child_global_id})
            hold = self.env['compassion.hold'].create(
                mapping.get_vals_from_connect(hold_data))
            child.hold_id = hold
            return [hold.id]

        return list()
