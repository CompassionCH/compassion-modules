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
from openerp.osv import fields, orm
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.config import config

from random import randint
from datetime import datetime

import requests
import logging
import traceback

logger = logging.getLogger(__name__)


class gmc_message_pool_process(orm.TransientModel):
    _name = 'gmc.message.pool.process'

    def process_messages(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids')
        self.pool.get('gmc.message.pool').process_messages(
            cr, uid, active_ids, context=context)
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


class gmc_message_pool(orm.Model):
    """ Pool of messages exchanged between Compassion CH and GMC. """
    _name = 'gmc.message.pool'

    _order = 'date desc'

    def _get_object_id(self, cr, uid, ids, field_name, args, context=None):
        res = dict()
        model_mapping = {
            'partner_id': 'res.partner',
            'child_id': 'compassion.child',
            'project_id': 'compassion.project',
            'invoice_line_id': 'account.invoice.line'
        }
        for message in self.browse(cr, uid, ids, context):
            if message.action_id.model == model_mapping[field_name]:
                res[message.id] = message.object_id
            elif message.action_id.model == 'recurring.contract':
                contract = self.pool.get('recurring.contract').browse(
                    cr, uid, message.object_id, context)
                if field_name == 'partner_id':
                    res[message.id] = contract.partner_id.id
                elif field_name == 'child_id':
                    res[message.id] = contract.child_id.id
                elif field_name == 'invoice_line_id':
                    invl_ids = self.pool.get('account.invoice.line').search(
                        cr, uid, [('contract_id', '=', contract.id),
                                  ('last_payment', '!=', False)],
                        order='due_date asc', context=context)
                    res[message.id] = invl_ids[0] if invl_ids else False
                else:
                    res[message.id] = False
        return res

    _columns = {
        'name': fields.related(
            'action_id', 'name', type="char", store=False, readonly=True
        ),
        'description': fields.related(
            'action_id', 'description', type="text",
            string=_("Action to execute"), store=False, readonly=True
        ),
        'direction': fields.related(
            'action_id', 'direction', type="char", store=True
        ),
        'partner_id': fields.function(
            _get_object_id, type='many2one', obj='res.partner',
            string=_("Partner"), store=True),
        'child_id': fields.function(
            _get_object_id, type='many2one', obj='compassion.child',
            string=_("Child"), store=True),
        'project_id': fields.function(
            _get_object_id, type='many2one', obj='compassion.project',
            string=_("Project"), store=True),
        'request_id': fields.char('Unique request ID', readonly=True),
        'date': fields.datetime(_('Message Date'), required=True),
        'action_id': fields.many2one(
            'gmc.action', _('GMC Message'), ondelete="restrict",
            required=True, readonly=True),
        'process_date': fields.datetime(_('Process Date'), readonly=True),
        'state': fields.selection(
            [('new', _('New')),
             ('pending', _('Pending')),
             ('fondue', _('To deliver')),
             ('success', _('Success')),
             ('failure', _('Failure'))],
            _('State'), readonly=True
        ),
        'failure_reason': fields.text(_("Failure details")),
        'object_id': fields.integer(_('Referrenced Object Id')),
        'incoming_key': fields.char(
            _('Incoming Reference'), size=9, readonly=True,
            help=_("In case of incoming message, contains the reference of "
                   "the child or project that will be created/modified.")),
        'event': fields.char(_('Incoming Event'), size=24, readonly=True,
                             help=_("Contains the event that triggered the "
                                    "incoming message.")),
        'partner_country_code': fields.char(_('Partner Country Code'), size=2),
        # Gift Type Messages information
        'invoice_line_id': fields.function(
            _get_object_id, type='many2one', obj='account.invoice.line',
            store=True),
        'gift_type': fields.related(
            'invoice_line_id', 'product_id', 'name', type='char',
            string=_('Gift type'), readonly=True, store=True),
        'gift_instructions': fields.related(
            'invoice_line_id', 'gift_instructions', type='char',
            string=_('Gift instructions'), store=True),
        'gift_amount': fields.related(
            'invoice_line_id', 'price_subtotal', type='float',
            string=_('Gift amount'), readonly=True, store=True),
        'money_sent_date': fields.datetime(_("Money sent"), readonly=True),
    }

    _defaults = {
        'date': str(datetime.today()),
        'state': 'new'
    }

    _sql_constraints = [(
        'request_id_uniq', 'UNIQUE(request_id)',
        _("You cannot have two requests with same id.")
    )]

    def process_update_messages(self, cr, uid, context=None):
        gmc_action_ids = self.pool.get('gmc.action').search(
            cr, uid,
            [('type', '=', 'update'), ('direction', '=', 'in')],
            context=context)
        gmc_update_messages_ids = self.search(
            cr, uid, [('action_id', 'in', gmc_action_ids)], context=context)
        self.process_messages(cr, uid, gmc_update_messages_ids, context)

    def process_messages(self, cr, uid, ids, context=None):
        """ Process given messages in pool. """

        # Find company country codes
        company_obj = self.pool.get('res.company')
        company_ids = company_obj.search(cr, uid, [], context=context)
        companies = company_obj.browse(cr, uid, company_ids, context)
        country_codes = [company.partner_id.country_id.code
                         for company in companies]

        today = datetime.now()
        for message in self.browse(cr, uid, ids, context=context):
            mess_date = datetime.strptime(message.date[:10], DF)
            if message.state == 'new' and (mess_date <= today or
                                           context.get('force_send')):
                res = False
                action = message.action_id
                if action.direction == 'in':
                    if message.partner_country_code in country_codes:
                        try:
                            res = self._perform_incoming_action(
                                cr, uid, message, context)
                        except Exception:
                            message = self.browse(cr, uid, message.id,
                                                  context)
                            message.write({
                                'state': 'failure',
                                'failure_reason': traceback.format_exc()})
                            if message.child_id and \
                                    message.child_id.state != 'E':
                                # Put child in error state
                                message.child_id.write({
                                    'previous_state': message.child_id.state,
                                    'state': 'E'})
                    else:
                        message.write({
                            'state': 'failure',
                            'failure_reason': 'Wrong Partner Country'})
                        res = False

                elif action.direction == 'out':
                    res = self._perform_outgoing_action(cr, uid, message,
                                                        context)
                else:
                    raise NotImplementedError

                if res:
                    message_update = {
                        'state': 'pending' if action.direction == 'out'
                        else 'success',
                        'process_date': today}
                    if isinstance(res, basestring):
                        message_update['request_id'] = res
                    message.write(message_update)
                    # Commit all changes of triggered by message before
                    # processing the next message.
                    cr.commit()

            elif message.state == 'fondue':
                # Mark Money Sent for Gift Messages
                message.write({
                    'money_sent_date': today,
                    'state': 'success'
                })

            elif message.state == 'failure':
                # Set back to new
                message.reset_message()

        return True

    def reset_message(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'request_id': False,
            'state': 'new',
            'process_date': False,
            'failure_reason': False
        }, context)
        return True

    def _perform_incoming_action(self, cr, uid, message, context=None):
        """ This method defines what has to be done
        for each incoming message type. """
        action = message.action_id
        model_obj = self.pool.get(action.model)
        args = {
            'code': message.incoming_key,
            'date': message.date,
            'object_id': message.object_id,
            'event': message.event,
        }
        if action.type in ('allocate', 'deallocate', 'depart', 'update'):
            return getattr(model_obj, action.type)(cr, uid, args, context)
        else:
            raise orm.except_orm(
                _("Invalid Action"),
                _("No implementation found for method '%s'.") % (action.type))

    def _perform_outgoing_action(self, cr, uid, message, context=None):
        """ Process an outgoing message by sending it to the middleware.
            Returns : unique id of generated request, or False.
        """
        action = message.action_id
        object_id = message.object_id
        if context is None:
            context = dict()
        if self._validate_outgoing_action(cr, uid, message, context):
            if context.get('test_mode'):
                # Don't send the request when testing.
                return 'test-uid' + str(randint(0, 999))
            server_url = config.get('middleware_url')
            if not server_url:
                raise orm.except_orm(
                    'ConfigError', _('No middleware server url specified in '
                                     'conf file'))
            url = server_url + action.type + '/' + \
                action.model + '/' + str(object_id)
            r = requests.get(url)
            if not r.status_code == 200:
                logger.error('Failing url: ' + url)
                raise orm.except_orm(
                    _('NetworkError'),
                    _('An error occured while sending message.'))
            json_data = r.json()
            logger.debug(r.text)
            success = json_data.get('success')
            if success == 'yes':
                return json_data.get('uuid')

        return False

    def _validate_outgoing_action(self, cr, uid, message, context=None):
        """ Validation of outgoing messages before sending them to GMC. """
        action = message.action_id
        object_id = message.object_id
        if action.name == 'CreateCommitment':
            contract = self.pool.get(action.model).browse(
                cr, uid, object_id, context=context)
            # Check that the constituent is known by GMC.
            partner = contract.correspondant_id
            message_ids = self.search(cr, uid, [
                ('name', '=', 'UpsertConstituent'),
                ('partner_id', '=', partner.id),
                ('state', '=', 'success')], context=context)
            if not message_ids:
                raise orm.except_orm(
                    _("Constituent (%s) not sent to GMC") % partner.name,
                    _("Please send the new constituents to GMC before sending"
                      " the commitments."))

            # Check that the contract is linked to a child
            child_id = contract.child_id
            if not child_id:
                raise orm.except_orm(
                    _("Contract is not a sponsorship."),
                    _("The new commitment of %s is not linked to a child and "
                      "should not be sent to GMC.") % partner.name)
            else:
                # Check that there are no previous sponsorship cancellation
                # pending.
                message_ids = self.search(
                    cr, uid, [
                        ('name', '=', 'CancelCommitment'),
                        ('child_id', '=', child_id.id),
                        ('state', 'in', ('new', 'pending'))], context=context)
                if message_ids:
                    raise orm.except_orm(
                        _("Commitment not sent (%s).") % child_id.code,
                        _("Please send the previous commitment cancellation "
                          "before the creation of a new commitment."))

        elif action.name == 'CreateGift':
            # Check that the commitment is known by GMC.
            invoice_line = self.pool.get(action.model).browse(
                cr, uid, object_id, context=context)
            contract = invoice_line.contract_id
            if contract and contract.correspondant_id and contract.child_id:
                message_ids = self.search(
                    cr, uid, [
                        ('name', '=', 'CreateCommitment'),
                        ('object_id', '=', contract.id),
                        ('state', '=', 'success')], context=context)
                if not message_ids:
                    raise orm.except_orm(
                        _("Commitment not sent to GMC (%s - %s)") % (
                            contract.partner_id.ref, contract.child_id.code),
                        _("The commitment the gift refers to was not "
                          "sent to GMC."))
            else:
                raise orm.except_orm(
                    _("Unknown sponsorship."),
                    _("The gift (%s - %s) is not related to a sponsorship so "
                      "it should not be sent to GMC.") % (
                        invoice_line.partner_id.name, invoice_line.name))

        elif action.name == 'CancelCommitment':
            # Check that the commitment is known by GMC.
            message_ids = self.search(
                cr, uid, [
                    ('name', '=', 'CreateCommitment'),
                    ('object_id', '=', object_id), ('state', '=', 'success')],
                context=context)
            if not message_ids:
                contract = self.pool.get(action.model).browse(
                    cr, uid, object_id, context=context)
                raise orm.except_orm(
                    _("Commitment not sent to GMC (%s - %s)") % (
                        contract.partner_id.ref, contract.child_id.code),
                    _("The commitment was not sent to GMC and therefore "
                      "cannot be cancelled."))

        return True

    def ack(self, cr, uid, request_id, status, message=None, context=None):
        """Message Acknowledgement meaning GMC has received our outgoing
        request.
        """
        message_ids = self.search(
            cr, uid, [('request_id', '=', request_id)], context=context)
        state = status.lower()
        for m in self.browse(cr, uid, message_ids, context):
            if state == 'success' and m.action_id.name == 'CreateGift':
                state = 'fondue'
            m.write({
                # Gift messages are in success mode only after money is sent.
                'state': state,
                'failure_reason': message
            })
        if not message_ids:
            logger.error('Request id not found:' + str(request_id))
        return True

    def create(self, cr, uid, vals, context=None):
        """ Directly put CreateGift messages which have a too long instruction
        in Failed state. """
        res_id = super(gmc_message_pool, self).create(cr, uid, vals, context)
        message = self.browse(cr, uid, res_id, context)
        if message.gift_instructions and len(message.gift_instructions) > 60:
            message.write({
                'state': 'failure',
                'failure_reason': _('Gift instructions is more than 60 '
                                    'characters length')})
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        """Propagate Gift instruction into invoice object."""
        if 'gift_instructions' in vals:
            if len(vals['gift_instructions']) > 60:
                vals.update({
                    'state': 'failure',
                    'failure_reason': _('Gift instructions is more than 60 '
                                        'characters length')})
            for message in self.browse(cr, uid, ids, context):
                message.invoice_line_id.write({
                    'name': vals['gift_instructions']})

        return super(gmc_message_pool, self).write(cr, uid, ids, vals,
                                                   context)


class gmc_action(orm.Model):
    """
    A GMC Action defines what has to be done for a specific OffRamp
    message of the Compassion International specification.

    A GMC Action can be originated either from an incoming or an outgoing
    message read from the GMC Message Pool class.

    Incoming actions :
        - Execute a method of a given OpenERP Object.
        - Each incoming action should map to some code to execute defined
          in the _perform_incoming_action() method.

    Outgoing actions :
        - Execute a method by calling Buckhill's middleware.
    """
    _name = 'gmc.action'

    def _get_message_types(self, cr, uid, context=None):
        res = self._get_incoming_message_types(
        ) + self._get_outgoing_message_types()
        # Extend with methods for both incoming and outgoing messages.
        res.append(
            ('update', 'Update Object'),
        )

        return res

    def _get_incoming_message_types(self):
        """ Incoming message types calling specific method on an object.
            The method should exist on the given model.
        """
        return [
            ('allocate', 'Allocate new Child'),
            ('deallocate', 'Deallocate Child'),
            ('depart', 'Depart Child'),
        ]

    def _get_outgoing_message_types(self):
        """ Outgoing messages sent to the middleware. """
        return [
            ('create', 'Create object'),
            ('cancel', 'Cancel object'),
            ('upsert', 'Create or Update object'),
        ]

    _columns = {
        'direction': fields.selection(
            (('in', _('Incoming Message')),
             ('out', _('Outgoing Message')),
             ),
            _('Message Direction'), required=True
        ),
        'name': fields.char(_('GMC Message'), size=20, required=True),
        'model': fields.char('OSV Model', size=30),
        'type': fields.selection(_get_message_types, _('Action Type'),
                                 required=True),
        'description': fields.text(_('Action to execute')),
    }

    def create(self, cr, uid, values, context={}):
        direction = values.get('direction', False)
        model = values.get('model', False)
        action_type = values.get('type', False)

        if self._validate_action(direction, model, action_type):
            return super(gmc_action, self).create(cr, uid, values,
                                                  context=context)
        else:
            raise orm.except_orm(
                _("Creation aborted."),
                _("Invalid action (%s, %s, %s).") % (
                    direction, model, action_type))

    def _validate_action(self, direction, model, action_type, context=None):
        """ Test if the action can be performed on given model. """
        if direction and model and action_type:
            if direction == 'in':
                model_obj = self.pool.get(model)
                return hasattr(model_obj, action_type)
            elif direction == 'out':
                return True

        return False

    def get_action_id(self, cr, uid, name, context=None):
        """ Returns the id of the action given its name. """
        action_id = self.search(cr, uid, [('name', '=', name)], limit=1,
                                context=context)
        if action_id:
            return action_id[0]
        else:
            return False
