# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from ..tools.onramp_connector import OnrampConnector
from ..mappings import base_mapping as mapping

from openerp import api, models, fields, _
from openerp.exceptions import Warning

from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession

from datetime import datetime

import logging
import traceback
import simplejson as json
logger = logging.getLogger(__name__)


class GmcMessagePoolProcess(models.TransientModel):
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


class GmcMessagePool(models.Model):
    """ Pool of messages exchanged between Compassion CH and GMC. """
    _name = 'gmc.message.pool'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Connect Message'

    _order = 'date desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(
        related='action_id.name', readonly=True)
    description = fields.Text(
        'Action to execute', related='action_id.description', readonly=True)
    direction = fields.Selection(related='action_id.direction', store=True)
    object_id = fields.Integer('Resource')
    object_ids = fields.Char(
        'Related records', help='Used for incoming messages containing '
                                'several records. (ids separated by commas)')
    res_name = fields.Char(compute='_compute_res_name', store=True)
    partner_id = fields.Many2one('res.partner', 'Partner')

    request_id = fields.Char('Unique request ID', readonly=True)
    date = fields.Datetime(
        'Message Date', required=True,
        default=fields.Datetime.now())
    action_id = fields.Many2one(
        'gmc.action', 'GMC Message', ondelete='restrict',
        required=True, readonly=True)
    process_date = fields.Datetime(readonly=True, track_visibility='onchange')
    state = fields.Selection(
        [('new', _('New')),
         ('pending', _('Pending')),
         ('success', _('Success')),
         ('failure', _('Failure'))],
        'State', readonly=True, default='new', track_visibility='always')
    failure_reason = fields.Text(
        'Failure details', track_visibility='onchange')
    headers = fields.Text()
    content = fields.Text()

    _sql_constraints = [
        ('request_id_uniq', 'UNIQUE(request_id)',
         _("You cannot have two requests with same id."))]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends('object_id', 'action_id')
    def _compute_res_name(self):
        for message in self:
            try:
                res_object = self.env[message.action_id.model].browse(
                    message.object_id)
                if res_object:
                    message.res_name = res_object.name
            except KeyError:
                message.res_name = 'Unknown'

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        message = super(GmcMessagePool, self).create(vals)
        if message.action_id.auto_process:
            message.process_messages()
        return message

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def update_res_name(self):
        self._compute_res_name()

    @api.multi
    def process_messages(self):
        new_messages = self.filtered(lambda m: m.state in ('new', 'failure'))
        new_messages.write({'state': 'pending', 'failure_reason': False})
        if self.env.context.get('async_mode', True):
            session = ConnectorSession.from_env(self.env)
            process_messages_job.delay(session, self._name, self.ids)
        else:
            self._process_messages()
        return True

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def force_success(self):
        self.write({'state': 'success', 'failure_reason': False})
        return True

    @api.multi
    def reset_message(self):
        self.write({
            'request_id': False,
            'state': 'new',
            'process_date': False,
            'failure_reason': False
        })
        return True

    @api.multi
    def open_related(self):
        self.ensure_one()
        if self.direction == 'out':
            # Outgoing messages are always related to one object.
            return {
                'name': 'Related object',
                'type': 'ir.actions.act_window',
                'res_model': self.action_id.model,
                'res_id': self.object_id,
                'view_type': 'form',
                'view_mode': 'form',
            }
        else:
            # Incoming messages can be related to several objects.
            res_ids = self.object_ids.split(',')
            return {
                'name': 'Related object',
                'type': 'ir.actions.act_window',
                'res_model': self.action_id.model,
                'domain': [('id', 'in', res_ids)],
                'view_type': 'form',
                'view_mode': 'tree,form',
            }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _process_messages(self):
        """ Process given messages in pool. """
        today = datetime.now()
        messages = self.filtered(lambda mess: mess.state == 'pending')
        if not self.env.context.get('force_send'):
            messages = messages.filtered(
                lambda mess: fields.Datetime.from_string(mess.date) <= today)

        # Verify all messages have the same action (cannot execute multiple
        # actions at once)
        action = messages.mapped('action_id')
        if len(action) > 1:
            raise Warning(_("Cannot process several actions at the same "
                            "time. Please process each message type "
                            "individually."))
        elif not action:
            # No messages pending
            return True

        message_update = {'process_date': fields.Datetime.now()}
        if action.direction == 'in':
            try:
                message_update.update(self._perform_incoming_action())
            except Exception:
                # Abort pending operations
                self.env.cr.rollback()
                self.env.invalidate_all()
                # Write error
                message_update.update({
                    'state': 'failure',
                    'failure_reason': traceback.format_exc()})

        elif action.direction == 'out':
            try:
                self._perform_outgoing_action()
            except Warning as e:
                # Put the messages in failure state
                self.write({
                    'state': 'failure',
                    'failure_reason': e.args[1]
                })
                self.env.cr.commit()
                raise
        else:
            raise NotImplementedError

        self.write(message_update)

        return True

    def _perform_incoming_action(self):
        """ Convert the data incoming from Connect into Odoo object values
        and call the process_commkit method on the related object. """
        action = self.action_id
        model_obj = self.env[action.model]
        commkit_data = json.loads(self.content)
        object_ids = model_obj.process_commkit(commkit_data)
        return {
            'state': 'success' if object_ids else 'failure',
            'object_ids': ','.join(object_ids)
        }

    def _perform_outgoing_action(self):
        """ Send a message to Compassion Connect"""
        # Load objects
        action = self.mapped('action_id')
        data_objects = self.env[action.model].with_context(
            lang='en_US').browse(self.mapped('object_id'))
        # Notify objects sent to connect for special handling if needed.
        if hasattr(data_objects, 'on_send_to_connect'):
            data_objects.on_send_to_connect()

        object_mapping = mapping.new_onramp_mapping(action.model, self.env)
        if action.connect_outgoing_wrapper:
            # Send multiple objects in a single message to GMCs
            message_data = {action.connect_outgoing_wrapper: list()}
            for data_object in data_objects:
                message_data[action.connect_outgoing_wrapper].append(
                    object_mapping.get_connect_data(data_object)
                )
            self._send_message(message_data)

        else:
            # Send individual message for each object
            for data_object in data_objects:
                message_data = object_mapping.get_connect_data(data_object)
                self._send_message(message_data)

    def _send_message(self, message_data):
        """Sends the prepared message and gets the answer from GMC."""
        action = self.mapped('action_id')
        onramp = OnrampConnector()
        onramp_answer = onramp.send_message(
            action.connect_service, action.request_type, message_data)
        if 200 <= onramp_answer['code'] < 300:
            # Success, loop through answer to get individual results
            data_objects = self.env[action.model].with_context(
                lang='en_US').browse(self.mapped('object_id'))
            results = onramp_answer.get('content', {}).get(
                action.connect_answer_wrapper, [])
            object_mapping = mapping.new_onramp_mapping(action.model, self.env)
            for i in range(0, len(results)):
                result = results[i]
                content_sent = message_data.get(
                    action.connect_outgoing_wrapper, message_data)
                mess_vals = {
                    'content': json.dumps(content_sent[i]) if isinstance(
                        content_sent, list) else json.dumps(content_sent),
                    'request_id': onramp_answer.get('request_id', False)
                }
                if result.get('Code', 2000) == 2000:
                    # Individual message was successfully processed
                    data_objects[i].write(
                        object_mapping.get_vals_from_connect(result))
                    mess_vals['state'] = 'success'
                else:
                    mess_vals.update({
                        'state': 'failure',
                        'failure_reason': result['Message'],
                    })
                self[i].write(mess_vals)
        else:
            # Complete failure (messages were not processed)
            fail = onramp_answer.get('content', {
                'Error': onramp_answer.get('Error', 'None')})
            self.write({
                'state': 'failure',
                'failure_reason':
                    '[%s] %s' % (onramp_answer['code'],
                                 str(fail.get('Error', 'None')))
            })

    def _validate_outgoing_action(self):
        """ Inherit to add message validation before sending it."""
        return True

    @api.model
    def _needaction_domain_get(self):
        return [('state', 'in', ('new', 'pending'))]


##############################################################################
#                            CONNECTOR METHODS                               #
##############################################################################
def related_action_messages(session, job):
    message_ids = job.args[1]
    action = {
        'name': _("Messages"),
        'type': 'ir.actions.act_window',
        'res_model': 'gmc.message.pool',
        'domain': [('id', 'in', message_ids)],
        'view_type': 'form',
        'view_mode': 'tree,form',
    }
    return action


@job(default_channel='root.gmc_pool')
@related_action(action=related_action_messages)
def process_messages_job(session, model_name, message_ids):
    """Job for processing messages."""
    messages = session.env[model_name].browse(message_ids)
    messages._process_messages()
