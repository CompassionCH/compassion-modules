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
    object_id = fields.Integer('Related Id')

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

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.one
    def _process_messages(self):
        """ Process given messages in pool. """
        today = datetime.now()
        mess_date = fields.Datetime.from_string(self.date)

        if self.state == 'pending' and (mess_date <= today or
                                        self.env.context.get('force_send')):
            message_update = {'process_date': fields.Datetime.now()}
            action = self.action_id
            if action.direction == 'in':
                try:
                    message_update.update(self._perform_incoming_action())
                except Exception:
                    # Abort pending operations
                    self.env.cr.rollback()
                    self.env.invalidate_all()
                    # Write error
                    self.write({
                        'state': 'failure',
                        'failure_reason': traceback.format_exc()})

            elif action.direction == 'out':
                try:
                    message_update.update(self._perform_outgoing_action())
                except Warning as e:
                    # Put the message in failure state
                    self.write({
                        'state': 'failure',
                        'failure_reason': e.args[1]
                    })
                    self.env.cr.commit()
                    raise
            else:
                raise NotImplementedError

            self.write(message_update)
            # Commit all changes of triggered by message before
            # processing the next message.
            self.env.cr.commit()

        return True

    def _perform_incoming_action(self):
        """ Convert the data incoming from Connect into Odoo object values
        and call the process_commkit method on the related object. """
        action = self.action_id
        model_obj = self.env[action.model]
        commkit_data = json.loads(self.content)
        object_mapping = mapping.new_onramp_mapping(action.model, self.env)
        object_data = object_mapping.get_vals_from_connect(commkit_data)
        object_id = model_obj.process_commkit(object_data)
        return {
            'state': 'success' if object_id else 'failure',
            'object_id': object_id
        }

    def _perform_outgoing_action(self):
        """ Send a message to Compassion Connect"""
        action = self.action_id
        data_object = self.env[action.model].browse(self.object_id)
        result = {
            'process_date': fields.Datetime.now()
        }
        if hasattr(data_object, 'convert_for_connect') and \
                hasattr(data_object, 'get_connect_data'):
            message_data = data_object.convert_for_connect()
            onramp = OnrampConnector()
            onramp_answer = onramp.send_message(
                action.connect_service, action.request_type, message_data)
            if 200 <= onramp_answer['code'] < 300:
                # TODO : see if this is not too specific
                connect_data = onramp_answer['content']['Responses'][0]
                data_object.get_connect_data(connect_data)
                result.update({
                    'state': 'success',
                    'request_id': onramp_answer.get('request_id', False),
                })
            else:
                result.update({
                    'state': 'failure',
                    'failure_reason':
                        '[%s] %s' % (onramp_answer['code'],
                                     str(onramp_answer.get('Error')))
                })
        else:
            result.update({
                'state': 'failure',
                'failure_reason': 'Object {} has no attributes '
                'convert_for_connect(), get_connect_data()'.format(
                    action.model)})
        return result

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
