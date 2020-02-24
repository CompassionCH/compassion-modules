##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from datetime import datetime, timedelta
from functools import reduce
from enum import Enum

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import config

logger = logging.getLogger(__name__)
test_mode = config.get('test_enable')


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
        domain=[('share', '=', False)], readonly=False
    )
    secondary_owner = fields.Char()
    ambassador = fields.Many2one('res.partner', readonly=False)
    yield_rate = fields.Integer()
    no_money_yield_rate = fields.Integer()
    channel = fields.Selection([
        ('web', 'Website'),
        ('event', 'Event'),
        ('ambassador', 'Ambassador'),
        ('sponsor_cancel', 'Sponsor Cancel'),
        ('sub', 'SUB Sponsorship'),
    ])
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
        return datetime.now() + diff

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
    _inherit = ['compassion.abstract.hold', 'mail.thread',
                'compassion.mapped.model']
    _description = 'Compassion hold'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    hold_id = fields.Char(readonly=True, track_visibility='onchange')
    child_id = fields.Many2one(
        'compassion.child', 'Child on hold', readonly=True
    )
    state = fields.Selection([
        ('draft', "Draft"),
        ('active', "Active"),
        ('expired', "Expired")],
        readonly=True, default='draft', track_visibility='onchange')
    reinstatement_reason = fields.Char(readonly=True)
    reservation_id = fields.Many2one('compassion.reservation', 'Reservation', readonly=False)
    no_money_extension = fields.Integer(
        help="Counts how many time the no money hold was extended."
    )

    # Track field changes
    ambassador = fields.Many2one(track_visibility='onchange', readonly=False)
    primary_owner = fields.Many2one(track_visibility='onchange', readonly=False)
    type = fields.Selection(track_visibility='onchange')
    channel = fields.Selection(track_visibility='onchange')
    expiration_date = fields.Datetime(track_visibility='onchange')

    _sql_constraints = [
        ('hold_id', 'unique(hold_id)',
         'The hold already exists in database.'),
    ]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        # Avoid duplicating Holds
        hold_id = vals.get('hold_id')
        if hold_id:
            hold = self.search([('hold_id', '=', hold_id)])
            if hold:
                hold.write(vals)
                return hold
        return super().create(vals)

    @api.multi
    def write(self, vals):
        res = super().write(vals)
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
        inactive_children = inactive_holds.mapped('child_id').filtered(
            lambda c: not c.hold_id)
        inactive_children.child_released()
        super(CompassionHold, inactive_holds).unlink()
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def update_hold(self):
        message_obj = self.env['gmc.message'].with_context(
            async_mode=False)
        action_id = self.env.ref('child_compassion.create_hold').id
        messages = message_obj
        for hold in self:
            message_vals = {
                'action_id': action_id,
                'object_id': hold.id,
                'child_id': hold.child_id.id,
            }
            messages += message_obj.create(message_vals)
        messages.process_messages()
        failed = messages.filtered(lambda m: m.state == 'failure')
        if failed:
            self.env.cr.rollback()
            raise UserError('\n\n'.join(failed.mapped('failure_reason')))

    @api.multi
    def hold_sent(self, vals):
        """ Called when hold is sent to Connect. """
        self.write(vals)
        # update compassion children with hold_id received
        for hold in self:
            child_to_update = hold.child_id
            if hold.hold_id:
                hold.state = 'active'
                if not child_to_update.hold_id:
                    child_to_update.child_consigned(hold.id)
                # Always commit after receiving a hold to avoid losing it
                if not test_mode:
                    self.env.cr.commit()    # pylint: disable=invalid-commit
            else:
                # Release child if no hold_id received
                hold.unlink()
                child_to_update.child_released()

    @api.model
    def reinstatement_notification(self, commkit_data):
        """ Called when a child was Reinstated. """
        # Reinstatement holds are available for 90 days (Connect default)
        in_90_days = datetime.now() + timedelta(days=90)

        hold_data = commkit_data.get(
            'ReinstatementHoldNotification', commkit_data)
        vals = self.json_to_data(hold_data, 'new_reinstatement_notification')
        child_id = vals.get('child_id')
        if not child_id:
            raise ValueError("No child found")
        child = self.env['compassion.child'].browse(child_id)
        if child.state not in ('F', 'R'):
            raise UserError(_("Child is not departed."))
        vals.update({
            'expiration_date': in_90_days,
            'state': 'active',
            'comments': 'Child was reinstated! Be sure to propose it to its '
                        'previous sponsor.'
        })
        hold = self.create(vals)
        child.child_consigned(hold.id)

        # Update hold duration to what is configured
        hold.write({
            'expiration_date': self.get_default_hold_expiration(
                HoldType.REINSTATEMENT_HOLD)
        })

        child.get_lifecycle_event()

        return [hold.id]

    def reservation_to_hold(self, commkit_data):
        """ Called when a reservation gots converted to a hold. """
        hold_data = commkit_data.get(
            'ReservationConvertedToHoldNotification')
        child_global_id = hold_data and hold_data.get('Beneficiary_GlobalID')
        if child_global_id:
            child = self.env['compassion.child'].create({
                'global_id': child_global_id})
            hold = self.env['compassion.hold'].create(
                self.json_to_data(hold_data, 'reservation_to_hold'))
            hold.write({
                'state': 'active',
                'ambassador': hold.reservation_id.ambassador.id,
                'channel': hold.reservation_id.channel
            })
            child.child_consigned(hold.id)
            reservation = hold.reservation_id
            reservation_state = 'active'
            number_reserved = reservation.number_reserved + 1
            if number_reserved == reservation.number_of_beneficiaries or \
                    reservation.reservation_type == 'child':
                reservation_state = 'expired'
            reservation.write({
                'state': reservation_state,
                'number_reserved': number_reserved
            })

            # Notify reservation owner
            hold.sudo().message_post(
                body=_("A new hold has been created because of an existing "
                       "reservation."),
                subject=_(f"{child.local_id} - Reservation converted to hold"),
                partner_ids=hold.primary_owner.partner_id.ids,
                type='comment',
                subtype='mail.mt_comment',
                content_subtype='plaintext'
            )

            return [hold.id]

        return list()

    @api.multi
    def button_release_hold(self):
        """
        Prevent releasing No Money Holds!
        """
        if self.filtered(lambda h: h.type == HoldType.NO_MONEY_HOLD.value):
            raise UserError(_("You cannot release No Money Hold!"))
        return self.release_hold()

    @api.multi
    def release_hold(self):
        messages = self.env['gmc.message'].with_context(
            async_mode=False)
        action_id = self.env.ref('child_compassion.release_hold').id

        for hold in self:
            messages += messages.create({
                'action_id': action_id,
                'object_id': hold.id
            })
        messages.process_messages()
        try:
            with self.env.cr.savepoint():
                fail = messages.filtered('failure_reason').mapped(
                    'failure_reason')
                if fail:
                    logger.error("\n".join(fail))
                    # Force hold removal
                    self.hold_released()
        except:
            logger.error("Some holds couldn't be released.")
        return True

    @api.multi
    def hold_released(self, vals=None):
        """ Called when release message was successfully sent to GMC. """
        self.write({'state': 'expired'})
        self.mapped('child_id').child_released()
        return True

    @api.model
    def check_hold_validity(self):
        """
        Remove expired holds
        :return: True
        """
        holds = self.search([
            ('state', '=', 'draft')
        ])
        holds.unlink()
        return True

    @api.model
    def postpone_no_money_cron(self):
        # Search for expiring No Money Hold
        this_week_delay = datetime.now() + timedelta(days=7)
        holds = self.search([
            ('state', '=', 'active'),
            ('expiration_date', '<=', this_week_delay),
            ('type', 'in', [HoldType.NO_MONEY_HOLD.value,
                            HoldType.SUB_CHILD_HOLD.value])
        ])
        holds.postpone_no_money_hold()
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
                # return -1 is better than an empty list, as it allow us a
                # better error handling
                return [-1]
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

    @api.multi
    def postpone_no_money_hold(self, additional_text=None):
        """
        When a No Money Hold is expiring, this will extend the hold duration.
        Only 2 extensions are allowed, then the hold is not modified.
        Send a notification to hold owner.
        :return: None
        """
        settings = self.env['availability.management.settings']
        first_extension = settings.get_param('no_money_hold_duration')
        second_extension = settings.get_param('no_money_hold_extension')
        body_extension = (
            "The no money hold for child {local_id} was expiring on "
            "{old_expiration} and was extended to {new_expiration}."
            "{additional_text}"
        )
        body_expiration = (
            "The no money hold for child {local_id} will expire on "
            "{old_expiration}. The sponsorship will be cancelled on that "
            "date.{additional_text}"
        )
        for hold in self.filtered(lambda h: h.no_money_extension < 3):
            hold_extension = first_extension \
                if not hold.no_money_extension else second_extension
            new_hold_date = hold.expiration_date + timedelta(days=hold_extension)
            is_extended = hold.no_money_extension < 2
            next_extension = hold.no_money_extension
            if hold.type == HoldType.NO_MONEY_HOLD.value:
                next_extension += 1
            hold_vals = {
                'no_money_extension': next_extension,
            }
            if is_extended:
                hold_vals['expiration_date'] = new_hold_date
            old_date = hold.expiration_date
            hold.write(hold_vals)
            subject = "No money hold extension" if is_extended else \
                "No money hold expiration"
            body = body_extension if is_extended else body_expiration
            values = {
                'local_id': hold.child_id.local_id,
                'old_expiration': old_date,
                'new_expiration': new_hold_date.strftime("%d %B %Y"),
                'additional_text': additional_text or '',
            }
            hold.message_post(
                body=_(body.format(**values)),
                subject=_(subject),
                type='comment',
            )
            # Commit after hold is updated
            if not test_mode:
                self.env.cr.commit()  # pylint:disable=invalid-commit

    ##########################################################################
    #                              Mapping METHOD                            #
    ##########################################################################

    @api.multi
    def data_to_json(self, mapping_name=None):
        json_data = super().data_to_json(mapping_name)
        for key, val in json_data.copy().items():
            if not val:
                del json_data[key]
        # Read manually Primary Owner, to avoid security restrictions on
        # companies in case the owner is in another company.
        if len(self) == 1:
            json_data['PrimaryHoldOwner'] = self.primary_owner.sudo().name
        elif self:
            for i, hold in enumerate(self):
                json_data[i][
                    'PrimaryHoldOwner'] = hold.primary_owner.sudo().name
        return json_data
