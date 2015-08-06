# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models, fields, _
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.config import config

from random import randint
from datetime import datetime

import requests
import logging
import traceback

logger = logging.getLogger(__name__)


class gmc_message_pool_process(models.TransientModel):
    _name = 'gmc.message.pool.process'

    @api.multi
    def process_messages(self):
        active_ids = self.env.context.get('active_ids', [])
        self.env['gmc.message.pool'].browse(active_ids).process_messages()
        action = {
            'name': 'Message treated',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'views': [(False, 'tree'), (False, 'form')],
            'res_model': 'gmc.message.pool',
            'domain': [('id', 'in', active_ids)],
            'target': 'current',
        }

        return action


class gmc_message_pool(models.Model):
    """ Pool of messages exchanged between Compassion CH and GMC. """
    _name = 'gmc.message.pool'
    _inherit = 'mail.thread'
    _description = 'GMC Message'

    _order = 'date desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(
        related='action_id.name', readonly=True)
    description = fields.Text(
        'Action to execute', related='action_id.description', readonly=True)
    direction = fields.Selection(related='action_id.direction', store=True)
    partner_id = fields.Many2one(
        'res.partner', 'Partner', compute='_set_partner_id', store=True)
    child_id = fields.Many2one(
        'compassion.child', 'Child', compute='_set_child_id', store=True)
    project_id = fields.Many2one(
        'compassion.project', 'Project', compute='_set_project_id', store=True)
    request_id = fields.Char('Unique request ID', readonly=True)
    date = fields.Datetime(
        'Message Date', required=True,
        default=datetime.now().strftime(DF + ' %H:%M:%S'))
    action_id = fields.Many2one(
        'gmc.action', 'GMC Message', ondelete='restrict',
        required=True, readonly=True)
    process_date = fields.Datetime(readonly=True, track_visibility='onchange')
    state = fields.Selection(
        [('new', _('New')),
         ('pending', _('Pending')),
         ('fondue', _('To deliver')),
         ('success', _('Success')),
         ('failure', _('Failure'))],
        'State', readonly=True, default='new', track_visibility='always')
    failure_reason = fields.Text(
        'Failure details', track_visibility='onchange')
    object_id = fields.Integer('Referrenced Object Id')
    incoming_key = fields.Char(
        'Incoming Reference', size=9, readonly=True,
        help=_("In case of incoming message, contains the reference of "
               "the child or project that will be created/modified."))
    event = fields.Char(
        'Incoming Event', size=24, readonly=True,
        help=_("Contains the event that triggered the incoming message."))
    partner_country_code = fields.Char(size=2)
    # Gift Type Messages information
    invoice_line_id = fields.Many2one(
        'account.invoice.line', compute='_set_invoice_line_id', store=True)
    gift_type = fields.Char(
        related='invoice_line_id.product_id.name', readonly=True, store=True)
    gift_instructions = fields.Char(
        compute='_get_gift_instructions', inverse='_set_gift_instructions')
    gift_amount = fields.Float(
        related='invoice_line_id.price_subtotal', readonly=True, store=True)
    money_sent_date = fields.Datetime('Money sent', readonly=True)

    _sql_constraints = [(
        'request_id_uniq', 'UNIQUE(request_id)',
        _("You cannot have two requests with same id.")
    )]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.one
    @api.depends('object_id')
    def _set_partner_id(self):
        model = self.action_id.model
        if model == 'res.partner':
            self.partner_id = self.object_id
        elif model == 'recurring.contract':
            contract = self.env[model].browse(self.object_id)
            self.partner_id = contract.correspondant_id.id
        elif model == 'account.invoice.line':
            contract = self.env[model].browse(self.object_id).contract_id
            self.partner_id = contract.correspondant_id.id

    @api.one
    @api.depends('object_id')
    def _set_child_id(self):
        model = self.action_id.model
        if model == 'compassion.child':
            self.child_id = self.object_id
        elif model == 'recurring.contract':
            contract = self.env[model].browse(self.object_id)
            self.child_id = contract.child_id.id
        elif model == 'account.invoice.line':
            contract = self.env[model].browse(self.object_id).contract_id
            self.child_id = contract.child_id.id

    @api.one
    @api.depends('object_id')
    def _set_project_id(self):
        model = self.action_id.model
        if model == 'compassion.project':
            self.project_id = self.object_id

    @api.one
    @api.depends('object_id')
    def _set_invoice_line_id(self):
        model = self.action_id.model
        if model == 'account.invoice.line':
            self.invoice_line_id = self.object_id
        elif model == 'recurring.contract':
            invl_ids = self.env['account.invoice.line'].search([
                ('contract_id', '=', self.object_id),
                ('last_payment', '!=', False)], order='due_date asc').ids
            self.invoice_line_id = invl_ids[0] if invl_ids else False

    @api.depends('invoice_line_id')
    @api.one
    def _get_gift_instructions(self):
        self.gift_instructions = self.invoice_line_id.gift_instructions

    @api.one
    def _set_gift_instructions(self):
        self.invoice_line_id.name = self.gift_instructions

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Directly put CreateGift messages which have a too long instruction
        in Failed state. Compute Gift fields."""
        message = super(gmc_message_pool, self).create(vals)
        if message.name == 'CreateGift' and len(
                message.gift_instructions) > 60:
            message.write({
                'state': 'failure',
                'failure_reason': _('Gift instructions is more than 60 '
                                    'characters length')})
        return message

    @api.multi
    def write(self, vals):
        """Propagate Gift instruction into invoice object."""
        if 'gift_instructions' in vals:
            if len(vals['gift_instructions']) > 60:
                vals.update({
                    'state': 'failure',
                    'failure_reason': _('Gift instructions is more than 60 '
                                        'characters length')})
        return super(gmc_message_pool, self).write(vals)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.one
    def process_messages(self):
        """ Process given messages in pool. """

        # Find company country codes
        company_obj = self.env['res.company']
        companies = company_obj.search([])
        country_codes = companies.mapped('partner_id.country_id.code')
        today = datetime.now()
        mess_date = datetime.strptime(self.date[:10], DF)

        if self.state == 'new' and (mess_date <= today or
                                    self.env.context.get('force_send')):
            res = False
            action = self.action_id
            if action.direction == 'in':
                if self.partner_country_code in country_codes or \
                        self.env.context.get('test_mode'):
                    try:
                        res = self._perform_incoming_action()
                    except Exception:
                        self.write({
                            'state': 'failure',
                            'failure_reason': traceback.format_exc()})
                        if self.child_id and \
                                self.child_id.state != 'E':
                            # Put child in error state
                            self.child_id.write({
                                'previous_state': self.child_id.state,
                                'state': 'E'})
                else:
                    self.write({
                        'state': 'failure',
                        'failure_reason': 'Wrong Partner Country'})
                    res = False

            elif action.direction == 'out':
                res = self._perform_outgoing_action()
            else:
                raise NotImplementedError

            if res:
                message_update = {
                    'state': 'pending' if action.direction == 'out'
                    else 'success',
                    'process_date': today}
                if isinstance(res, basestring):
                    message_update['request_id'] = res
                self.write(message_update)
                # Commit all changes of triggered by message before
                # processing the next message.
                self.env.cr.commit()

        elif self.state == 'fondue':
            # Mark Money Sent for Gift Messages
            self.write({
                'money_sent_date': today,
                'state': 'success'})

        elif self.state == 'failure':
            # Set back to new
            self.write({
                'request_id': False,
                'state': 'new',
                'process_date': False,
                'failure_reason': False})

        return True

    @api.model
    def ack(self, request_id, status, message=None):
        """Message Acknowledgement meaning GMC has received our outgoing
        request.
        """
        messages = self.search([('request_id', '=', request_id)])
        state = status.lower()
        for m in messages:
            if state == 'success' and m.name == 'CreateGift':
                state = 'fondue'
            m.write({
                # Gift messages are in success mode only after money is sent.
                'state': state,
                'failure_reason': message
            })
        if not messages:
            logger.error('Request id not found:' + str(request_id))
        return True

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.model
    def process_update_messages(self):
        gmc_action_ids = self.env['gmc.action'].search(
            [('type', '=', 'update'), ('direction', '=', 'in')]).ids
        gmc_update_messages = self.search(
            [('action_id', 'in', gmc_action_ids)])
        gmc_update_messages.process_messages()

    @api.multi
    def force_success(self):
        self.write({'state': 'success', 'failure_reason': False})
        self.filtered(lambda m: m.name == 'CreateGift').write({
            'state': 'fondue'})
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.one
    def _perform_incoming_action(self):
        """ This method defines what has to be done
        for each incoming message type. """
        action = self.action_id
        model_obj = self.env[action.model]
        args = {
            'code': self.incoming_key,
            'date': self.date,
            'object_id': self.object_id,
            'event': self.event,
        }
        if action.type in ('allocate', 'deallocate', 'depart', 'update'):
            return getattr(model_obj, action.type)(args)
        else:
            raise Warning(
                _("Invalid Action"),
                _("No implementation found for method '%s'.") % (action.type))

    @api.one
    def _perform_outgoing_action(self):
        """ Process an outgoing message by sending it to the middleware.
            Returns : unique id of generated request, or False.
        """
        action = self.action_id
        object_id = self.object_id

        if self._validate_outgoing_action():
            if self.env.context.get('test_mode'):
                # Don't send the request when testing.
                return 'test-uid' + str(randint(0, 999))
            server_url = config.get('middleware_url')
            if not server_url:
                raise Warning(
                    'ConfigError',
                    _('No middleware server url specified in conf file'))
            url = server_url + action.type + '/' + \
                action.model + '/' + str(object_id)
            r = requests.get(url)
            if not r.status_code == 200:
                logger.error('Failing url: ' + url)
                raise Warning(
                    _('NetworkError'),
                    _('An error occured while sending message.'))
            json_data = r.json()
            logger.debug(r.text)
            success = json_data.get('success')
            if success == 'yes':
                return json_data.get('uuid')

        return False

    @api.one
    def _validate_outgoing_action(self):
        """ Validation of outgoing messages before sending them to GMC. """
        action = self.action_id
        object_id = self.object_id
        if action.name == 'CreateCommitment':
            contract = self.env[action.model].browse(object_id)
            # Check that the constituent is known by GMC.
            partner = contract.correspondant_id
            message_count = self.search_count([
                ('name', '=', 'UpsertConstituent'),
                ('partner_id', '=', partner.id),
                ('state', '=', 'success')])
            if not message_count:
                raise Warning(
                    _("Constituent (%s) not sent to GMC") % partner.name,
                    _("Please send the new constituents to GMC before sending"
                      " the commitments."))

            # Check that the contract is linked to a child
            child_id = contract.child_id
            if not child_id:
                raise Warning(
                    _("Contract is not a sponsorship."),
                    _("The new commitment of %s is not linked to a child and "
                      "should not be sent to GMC.") % partner.name)
            else:
                # Check that there are no previous sponsorship cancellation
                # pending.
                message_count = self.search_count([
                    ('name', '=', 'CancelCommitment'),
                    ('child_id', '=', child_id.id),
                    ('state', 'in', ('new', 'pending'))])
                if message_count:
                    raise Warning(
                        _("Commitment not sent (%s).") % child_id.code,
                        _("Please send the previous commitment cancellation "
                          "before the creation of a new commitment."))

        elif action.name == 'CreateGift':
            # Check that the commitment is known by GMC.
            invoice_line = self.invoice_line_id
            contract = invoice_line.contract_id
            if contract and 'S' in contract.type:
                message_count = self.search_count([
                    ('name', '=', 'CreateCommitment'),
                    ('object_id', '=', contract.id),
                    ('state', '=', 'success')])
                if not message_count:
                    raise Warning(
                        _("Commitment not sent to GMC (%s - %s)") % (
                            contract.partner_id.ref, contract.child_id.code),
                        _("The commitment the gift refers to was not "
                          "sent to GMC."))
            else:
                raise Warning(
                    _("Unknown sponsorship."),
                    _("The gift (%s - %s) is not related to a sponsorship so "
                      "it should not be sent to GMC.") % (
                        invoice_line.partner_id.name, invoice_line.name))

        elif action.name == 'CancelCommitment':
            # Check that the commitment is known by GMC.
            message_count = self.search_count([
                ('name', '=', 'CreateCommitment'),
                ('object_id', '=', object_id), ('state', '=', 'success')])
            if not message_count:
                contract = self.env[action.model].browse(object_id)
                raise Warning(
                    _("Commitment not sent to GMC (%s - %s)") % (
                        contract.partner_id.ref, contract.child_id.code),
                    _("The commitment was not sent to GMC and therefore "
                      "cannot be cancelled."))

        return True
