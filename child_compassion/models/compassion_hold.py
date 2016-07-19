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
            child = self.env['compassion.child'].search([
                ('id', '=', expired_hold.child_id.id)
            ])
            child.active = False

        for hold in expired_holds:
            hold.active = False
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
