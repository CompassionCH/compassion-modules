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
from enum import Enum

from datetime import datetime, timedelta

from openerp import api, models, fields, _
from openerp.exceptions import Warning

from ..mappings.child_reinstatement_mapping import ReinstatementMapping
from ..mappings.childpool_create_hold_mapping import ReservationToHoldMapping


class HoldType(Enum):
    """ Defines available Hold Types. """
    CHANGE_COMMITMENT_HOLD = 'Change Commitment Hold'
    CONSIGNMENT_HOLD = 'Consignment Hold'
    DELINQUENT_HOLD = 'Delinquent Mass Cancel Hold'
    E_COMMERCE_HOLD = 'E-Commerce Hold'
    NO_MONEY_HOLD = 'No Money Hold'
    REINSTATEMENT_HOLD = 'Reinstatement Hold'
    RESERVATION_HOLD = 'Reservation Hold'
    SPONSOR_CANCEL_HOLD = 'Sponsor Cancel Hold'
    SUB_CHILD_HOLD = 'Sub Child Hold'

    @staticmethod
    def get_hold_types():
        return [attr.value for attr in HoldType]

    @staticmethod
    def from_string(hold_type):
        """ Gets the HoldType given its string representation. """
        for etype in HoldType:
            if etype.value == hold_type:
                return etype
        return False


class AbstractHold(models.AbstractModel):
    """ Defines the basics of each model that must set up hold values. """
    _name = 'compassion.abstract.hold'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    type = fields.Selection(
        'get_hold_types', required=True,
        default=HoldType.CONSIGNMENT_HOLD.value
    )
    expiration_date = fields.Datetime(required=True)
    primary_owner = fields.Many2one(
        'res.users', required=True, default=lambda self: self.env.user,
        domain=[('share', '=', False)]
    )
    secondary_owner = fields.Char()
    ambassador = fields.Many2one('res.users')
    yield_rate = fields.Float()
    no_money_yield_rate = fields.Float()
    channel = fields.Selection('get_channel')
    source_code = fields.Char()
    comments = fields.Char()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def get_hold_types(self):
        return [(hold, hold) for hold in HoldType.get_hold_types()]

    @api.model
    def get_default_hold_expiration(self, hold_type):
        """
        Get the default hold expiration date.
        :param hold_type: HoldType Enum
        :return:
        """
        config_obj = self.env['availability.management.settings']
        hold_param = hold_type.name.lower() + '_duration'
        duration = config_obj.get_param(hold_param)
        diff = timedelta(days=duration) if hold_type != \
            HoldType.E_COMMERCE_HOLD else timedelta(minutes=duration)
        return fields.Datetime.to_string(datetime.now() + diff)

    @api.model
    def get_channel(self):
        return [
            ('web', _('Website')),
            ('event', _('Event')),
            ('ambassador', _('Ambassador')),
        ]

    @api.onchange('type')
    def onchange_type(self):
        default_hold = self.env.context.get('default_expiration_date')
        self.expiration_date = default_hold or \
            self.get_default_hold_expiration(HoldType.from_string(self.type))

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_fields(self):
        """ Returns the fields for which we want to know the value. """
        return ['type', 'expiration_date', 'primary_owner',
                'secondary_owner', 'yield_rate', 'no_money_yield_rate',
                'channel', 'source_code', 'comments', 'ambassador']

    def get_hold_values(self):
        """ Get the field values of one record.
            :return: Dictionary of values for the fields
        """
        self.ensure_one()
        vals = self.read(self.get_fields())[0]
        vals['primary_owner'] = vals['primary_owner'][0]
        ambassador = vals.get('ambassador')
        if ambassador:
            vals['ambassador'] = ambassador[0]
        del vals['id']
        return vals


class CompassionHold(models.Model):
    _name = 'compassion.hold'
    _rec_name = 'hold_id'
    _inherit = ['compassion.abstract.hold', 'mail.thread']

    hold_id = fields.Char(readonly=True)
    child_id = fields.Many2one(
        'compassion.child', 'Child on hold', readonly=True
    )
    state = fields.Selection([
        ('draft', "Draft"),
        ('active', "Active"),
        ('expired', "Expired")],
        readonly=True, default='draft', track_visibility='onchange')
    reinstatement_reason = fields.Char(readonly=True)
    reservation_id = fields.Many2one('compassion.reservation', 'Reservation')

    # Track field changes
    ambassador = fields.Many2one(track_visibility='onchange')
    primary_owner = fields.Many2one(track_visibility='onchange')
    type = fields.Selection(track_visibility='onchange')
    channel = fields.Selection(track_visibility='onchange')

    _sql_constraints = [
        ('hold_id', 'unique(hold_id)',
         'The hold already exists in database.'),
    ]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        res = super(CompassionHold, self).write(vals)
        notify_vals = ['primary_owner', 'type', 'expiration_date']
        notify = reduce(lambda prev, val: prev or val in vals, notify_vals,
                        False)
        if notify and not self.env.context.get('no_upsert'):
            self.update_hold()

        return res

    @api.multi
    def unlink(self):
        """
        Don't unlink active holds, but only those that don't relate to
        a child anymore (child released).
        :return: True
        """
        active_holds = self.filtered(lambda h: h.state == 'active')
        active_holds.release_hold()
        inactive_holds = self - active_holds
        inactive_children = inactive_holds.mapped('child_id')
        inactive_children.signal_workflow('release')
        invalid_holds = self.filtered(lambda h: not h.child_id)
        super(CompassionHold, invalid_holds).unlink()
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def update_hold(self):
        message_obj = self.env['gmc.message.pool'].with_context(
            async_mode=False)
        action_id = self.env.ref('child_compassion.create_hold').id

        message_vals = {
            'action_id': action_id,
            'object_id': self.id
        }
        message_obj.create(message_vals).process_messages()

    @api.multi
    def hold_sent(self, vals):
        """ Called when hold is sent to Connect. """
        self.write(vals)
        # update compassion children with hold_id received
        for hold in self:
            child_to_update = hold.child_id
            if hold.hold_id:
                hold.state = 'active'
                child_to_update.write({
                    'hold_id': hold.id,
                    'date': fields.Date.today(),
                })
            else:
                # Release child if no hold_id received
                hold.unlink()
                child_to_update.signal_workflow('release')

    @api.model
    def reinstatement_notification(self, commkit_data):
        """ Called when a child was Reinstated. """
        reinstatement_mapping = ReinstatementMapping(self.env)
        # Reinstatement holds are available for 90 days (Connect default)
        in_90_days = datetime.now() + timedelta(days=90)

        hold_data = commkit_data.get(
            'ReinstatementHoldNotification', commkit_data)
        vals = reinstatement_mapping.get_vals_from_connect(hold_data)
        child_id = vals.get('child_id')
        if not child_id:
            raise ValueError("No child found")
        vals.update({
            'expiration_date': fields.Datetime.to_string(in_90_days),
            'state': 'active'
        })
        hold = self.create(vals)
        child = self.env['compassion.child'].browse(child_id)
        child.hold_id = hold

        # Update hold duration to what is configured
        hold.write({
            'expiration_date': self.get_default_hold_expiration(
                HoldType.REINSTATEMENT_HOLD)
        })

        child.get_lifecycle_event()

        return [hold.id]

    def reservation_to_hold(self, commkit_data):
        """ Called when a reservation gots converted to a hold. """
        mapping = ReservationToHoldMapping(self.env)
        hold_data = commkit_data.get(
            'ReservationConvertedToHoldNotification')
        child_global_id = hold_data and hold_data.get('Beneficiary_GlobalID')
        if child_global_id:
            child = self.env['compassion.child'].create({
                'global_id': child_global_id})
            hold = self.env['compassion.hold'].create(
                mapping.get_vals_from_connect(hold_data))
            hold.state = 'active'
            child.hold_id = hold

            # Notify reservation owner
            hold.message_post(
                body="A new hold has been created because of an existing "
                "reservation.",
                subject="Reservation converted to hold",
                partner_ids=hold.primary_owner.partner_id.ids,
                type='comment',
                subtype='mail.mt_comment',
                content_subtype='plaintext'
            )

            return [hold.id]

        return list()

    @api.multi
    def release_hold(self):
        messages = self.env['gmc.message.pool'].with_context(
            async_mode=False)
        action_id = self.env.ref('child_compassion.release_hold').id

        for hold in self:
            messages += messages.create({
                'action_id': action_id,
                'object_id': hold.id
            })
        messages.process_messages()
        self.env.cr.commit()
        fail = messages.filtered('failure_reason').mapped('failure_reason')
        if fail:
            raise Warning(
                "\n".join(fail)
            )

        return True

    @api.multi
    def hold_released(self, vals=None):
        """ Called when release message was successfully sent to GMC. """
        self.write({'state': 'expired'})
        for child in self.mapped('child_id'):
            child.hold_id = False
            if child.sponsor_id:
                # Check if it was a depart and retrieve lifecycle event
                child.get_lifecycle_event()
            else:
                child.signal_workflow('release')
        return True

    @api.model
    def check_hold_validity(self):
        # Mark old holds as expired and release children if necessary
        holds = self.env['compassion.hold'].search([
            ('expiration_date', '<', fields.Datetime.now()),
            ('state', '=', 'active')
        ])
        holds.write({'state': 'expired'})
        holds.mapped('child_id').write({'hold_id': False})
        free_children = holds.mapped('child_id').filtered(
            lambda c: not c.sponsor_id)
        free_children.signal_workflow('release')

        # Remove holds that have no child linked anymore
        holds = self.env['compassion.hold'].search([
            ('state', '=', 'expired'),
            ('child_id', '=', False)
        ])
        holds.unlink()

        return True

    @api.model
    def beneficiary_hold_removal(self, commkit_data):
        data = commkit_data.get('BeneficiaryHoldRemovalNotification')
        hold = self.search([
            ('hold_id', '=', data.get('HoldID'))
        ])
        if not hold:
            child = self.env['compassion.child'].search([
                ('global_id', '=', data.get('Beneficiary_GlobalID'))
            ])
            if not child:
                return []
            hold = child.hold_id
            if not hold:
                hold = self.create({
                    'hold_id': data.get('HoldID'),
                    'expiration_date': fields.Datetime.now(),
                    'child_id': child.id,
                })

        hold.comments = data.get('NotificationReason')
        hold.hold_released()
        return [hold.id]
