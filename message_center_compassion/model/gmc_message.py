# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino. Copyright Compassion Suisse
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv.orm import Model
from openerp.osv import fields, osv
from openerp.tools.translate import _
import requests
import pdb
import datetime
import logging


SERVER_URL = 'https://test.services.compassion.ch:443/rest/openerp/'
logger = logging.getLogger(__name__)


class gmc_message_pool_process(osv.orm.TransientModel):
    _name = 'gmc.message.pool.process'
    
    def process_messages(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids')
        self.pool.get('gmc.message.pool').process_messages(cr, uid ,active_ids, context=context)
        action = {
            'name': 'Message treated',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'gmc.message.pool',
            'domain' : [('id','in',active_ids)],
            'target': 'current',
        }
        
        return action


class gmc_message_pool(Model):
    """ Pool of messages exchanged between Compassion CH and GMC. """
    _name = 'gmc.message.pool'


    _columns = {
        'name': fields.related(
            'action_id', 'name', type="char", store=False, readonly=True
        ),
        'description': fields.related(
            'action_id', 'description', type="text", string=_("Action to execute"), store=False, readonly=True
        ),
        'direction': fields.related(
            'action_id', 'direction', type="char", store=True
        ),
        'partner_id': fields.many2one(
            'res.partner', _("Partner")
        ),
        'child_id': fields.many2one(
            'compassion.child', _("Child")
        ),
        'date': fields.date(_('Message Date'), required=True),
        'action_id': fields.many2one('gmc.action',_('GMC Message'),
                                  ondelete="restrict", required=True),
        'process_date': fields.date(_('Process Date'), readonly=True),
        'state': fields.selection(
            [('pending', _('Pending')),
             ('sent', _('Processed'))],
            _('State'), readonly=True
        ),
        'object_id': fields.integer(_('Referrenced Object Id')),
        'incoming_key': fields.char(_('Incoming Reference'), size=9,
                                    help=_("In case of incoming message, "
                                           "contains the reference of the "
                                           "child or the project that will "
                                           "be created/modified.")),
    }
    
    _defaults = {
        'date' : str(datetime.date.today()),
        'state' : 'pending'
    }
    
    
    
    def process_messages(self, cr, uid, ids, context=None):
        """ Process given messages in pool. """
        success_ids = []
        for message in self.browse(cr, uid, ids, context=context):
            if message.state == 'pending':
                message_args = {'object_ref':message.incoming_key}
                if self.pool.get('gmc.action').execute(cr, uid, message.action_id.id, message.object_id, message_args, context=context):
                    success_ids.append(message.id)
                    
        if success_ids:
            self.write(cr, uid, success_ids, {'state':'sent','process_date':datetime.date.today()}, context=context)
            
        return True
                    
gmc_message_pool()


class gmc_action(Model):
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
        res = self._get_incoming_message_types() + self._get_outgoing_message_types()
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
            ('allocate','Allocate new Child'),
            ('deallocate', 'Deallocate Child'),
            ('depart', 'Depart Child'),
        ]
    
    def _get_outgoing_message_types(self):
        """ Outgoing messages sent to the middleware. """
        return [
            ('create','Create object'),
            ('cancel','Cancel object'),
            ('upsert','Create or Update object'),
        ]
    
    
    _columns = {
        'direction': fields.selection(
            (('in',_('Incoming Message')),
             ('out',_('Outgoing Message')),
            ),
            _('Message Direction'), required=True
        ),
        'name': fields.char(_('GMC Message'), size=20, required=True),
        'model': fields.char('OSV Model', size=30),
        'type': fields.selection(_get_message_types, _('Action Type'), required=True),
        'description': fields.text(_('Action to execute')),
    }
    
    
    def execute(self, cr, uid, id, object_id, args={}, context=None):
        """ Executes the action on the given object_id. 
        
            Args:
                - id: id of the action to be executed.
                - object_id: for incoming messages, object on which to perform the action.
                             for outgoing messages, object from which to read data.
                - args (dict): for incoming messages, optional arguments to be passed in the executed method.
        """
        action = self.browse(cr, uid, id, context=context)

        if action.direction == 'in':
            return self._perform_incoming_action(cr, uid, action, object_id, args=args, context=context)
        elif action.direction == 'out':
            return self._perform_outgoing_action(cr, uid, action, object_id, context=context)
        else:
            raise NotImplementedError
            
            
    def create(self, cr, uid, values, context={}):
        direction = values.get('direction', False)
        model = values.get('model', False)
        action_type = values.get('type', False)

        if self._validate_action(direction, model, action_type):
            return super(gmc_action, self).create(cr, uid, values, context=context)
        else:
            raise osv.except_osv(_("Creation aborted."), _("Invalid action (%s, %s, %s).") % (direction, model, action_type))
           
        
                
                
    def _perform_incoming_action(self, cr, uid, action, object_id, args={}, context=None):
        """ This method defines what has to be done for each incoming message type. """
        res = False
        model_obj = self.pool.get(action.model)
        if action.type == 'allocate':
            ref = args['object_ref']
            res = model_obj.allocate(cr, uid, ref, context=context)
        elif action.type in ('deallocate', 'depart', 'update'):
            res = getattr(model_obj, action.type)(cr, uid, object_id, context=context)
        else:
            raise osv.except_osv(_("Invalid Action"), _("No implementation found for method '%s'.") % (action.type))
            
        return res
    
    def _perform_outgoing_action(self, cr, uid, action, object_id, context=None):
        """ Process an outgoing message by sending it to the middleware. """
        if self._validate_outgoing_action(cr, uid, action, object_id, context=context):
            session = requests.Session()
            session.verify = False
            url = SERVER_URL + action.type + '/' + action.model + '/' + str(object_id)
            resp = session.get(url)
            content = resp.content
            
            # TODO : Parse response content to see if the operation succeeded
            logger.info("middleware response : " + content)
        
            return True
        
        else:
            return False
    
    def _validate_action(self, direction, model, action_type, context=None):
        """ Test if the action can be performed on given model. """
        if direction and model and action_type:
            if direction == 'in':
                model_obj = self.pool.get(model)
                return hasattr(model_obj, action_type)
            elif direction == 'out':
                return True
        
        return False
        
    def _validate_outgoing_action(self, cr, uid, action, object_id, context=None):
        """ Validation of outgoing messages before sending them to GMC. """
        message_obj = self.pool.get('gmc.message.pool')
        
        if action.name == 'CreateCommitment':
            contract = self.pool.get(action.model).browse(cr, uid, object_id, context=context)
            # Check that the constituent is known by GMC.
            partner = contract.partner_id
            message_ids = message_obj.search(cr, uid, [('object_id','=',partner.id),('state','=','sent')], context=context)
            if not message_ids:
                raise osv.except_osv(_("Constituent (%s) not sent to GMC") % partner.name, _("Please send the new constituents to GMC before sending the commitments."))
                            
            # Check that the contract is linked to a child
            child_id = contract.child_id
            if not child_id:
                raise osv.except_osv(_("Contract is not a sponsorship."),_("The new commitment of %s is not linked to a child and should not be sent to GMC.") % partner.name)
            else:
                # Check that there are no previous sponsorship cancellation pending.
                message_ids = message_obj.search(cr, uid, [('name','=','CancelCommitment'),('child_id','=',child_id.id),('state','=','pending')], context=context)
                if message_ids:
                    raise osv.except_osv(_("Commitment not sent (%s).") % child_id.code, _("Please send the previous commitment cancellation before the creation of a new commitment."))
                
        
        elif action.name == 'CreateGift':
            # Check that the commitment is known by GMC.
            invoice_line = self.pool.get(action.model).browse(cr, uid, object_id, context=context)
            contract = invoice_line.contract_id
            if contract and contract.partner_id and contract.child_id:
                message_ids = message_obj.search(cr, uid, [('name','=','CreateCommitment'),('object_id','=',contract.id),('state','=','sent')], context=context)
                if not message_ids:
                    raise osv.except_osv(_("Commitment not sent to GMC (%s - %s)") % (contract.partner_id.ref, contract.child_id.code), _("The commitment the gift refers to was not sent to GMC."))
            else:
                raise osv.except_osv(_("Unknown sponsorship."), _("The gift (%s - %s) is not related to a sponsorship so it should not be sent to GMC.") % (invoice_line.partner_id.name, invoice_line.name))
        
        
        elif action.name == 'CancelCommitment':
            # Check that the commitment is known by GMC.
            message_ids = message_obj.search(cr, uid, [('name','=','CreateCommitment'),('object_id','=',object_id),('state','=','sent')], context=context)
            if not message_ids:
                raise osv.except_osv(_("Commitment not sent to GMC (%s - %s)") % (contract.partner_id.ref, contract.child_id.code), _("The commitment was not sent to GMC and therefore cannot be cancelled."))

                
        return True
        
gmc_action()