# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class GmcAction(models.Model):
    """
    A GMC Action defines what has to be done for a specific
    message of the Compassion International specification.

    A GMC Action can be originated either from an incoming or an outgoing
    message read from the GMC Message Pool class.

    Incoming actions :
        - Calls a method 'incoming_method'
          ('process_commkit' by default) of the action model which must
          return a list of ids of the updated records.

    Outgoing actions :
        - The object can implement 'on_send_to_connect' method in order
          to execute some code before sending the object to GMC.
        - Calls 'success_method' (write by default) on the action model with
          the answer sent by GMC when message was successfully transmitted.
    """
    _name = 'gmc.action'

    direction = fields.Selection(
        [('in', _('Incoming Message')), ('out', _('Outgoing Message'))],
        'Message Direction', required=True)
    name = fields.Char('GMC Message', required=True)
    model = fields.Char('Model')
    description = fields.Text('Action to execute')
    mapping_id = fields.Many2one('compassion_mapping')
    connect_service = fields.Char(
        help='URL endpoint for sending messages to GMC'
    )
    connect_outgoing_wrapper = fields.Char(
        help='Tag in which multiple messages can be encapsulated'
    )
    connect_answer_wrapper = fields.Char(
        help='Tag in which answer is found (for outgoing messages)'
    )
    success_method = fields.Char(
        default='write',
        help='method to call on the object upon success delivery '
             '(will pass the received answer as parameter as dictionary)'
    )
    failure_method = fields.Char(
        help='method called on the object when the response contain error')

    incoming_method = fields.Char(
        default='process_commkit',
        help='method called on the object when receiving incoming message '
             '(will pass the received json as parameter as dictionary)'
    )
    batch_send = fields.Boolean(
        help='True if multiple objects can be sent through a single message'
    )
    auto_process = fields.Boolean(
        help='Set to True for processing the message as soon as it is created.'
    )
    request_type = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
    ])

    @api.multi
    @api.constrains('model', 'direction', 'incoming_method')
    def _validate_action(self):
        """ Test if the action can be performed on given model. """
        for action in self:
            valid = True
            model_obj = self.env[self.model]
            if action.direction == 'in':
                valid = hasattr(model_obj, action.incoming_method)

            if not valid:
                raise ValidationError(
                    _("Invalid action (%s, %s).") % (
                        action.direction, action.model))

    def get_action_id(self, name):
        """ Returns the id of the action given its name. """
        action_id = self.search([('name', '=', name)], limit=1)
        if action_id:
            return action_id.id
        return False
