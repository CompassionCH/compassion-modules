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
from openerp import api, models, fields, _
from openerp.exceptions import ValidationError


class GmcAction(models.Model):
    """
    A GMC Action defines what has to be done for a specific
    message of the Compassion International specification.

    A GMC Action can be originated either from an incoming or an outgoing
    message read from the GMC Message Pool class.

    Incoming actions :
        - Calls a method 'process_commkit' of the action model which must
          return a list of ids of the updated records.

    Outgoing actions :
        - The object can implement 'on_send_to_connect' method in order
          to execute some code before sending the object to GMC.
        - Calls a write on the action model with the
          answer sent by GMC when message was successfully transmitted.
    """
    _name = 'gmc.action'

    direction = fields.Selection(
        [('in', _('Incoming Message')), ('out', _('Outgoing Message'))],
        'Message Direction', required=True)
    name = fields.Char('GMC Message', size=20, required=True)
    model = fields.Char('OSV Model', size=30)
    description = fields.Text('Action to execute')
    connect_service = fields.Char(
        help='URL endpoint for sending messages to GMC'
    )
    connect_outgoing_wrapper = fields.Char(
        help='Tag in which multiple messages can be encapsulated'
    )
    connect_answer_wrapper = fields.Char(
        help='Tag in which answer is found (for outgoing messages)'
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

    @api.one
    @api.constrains('model', 'direction')
    def _validate_action(self):
        """ Test if the action can be performed on given model. """
        valid = True
        model_obj = self.env[self.model]
        if self.direction == 'in':
            valid = hasattr(model_obj, 'process_commkit')

        if not valid:
            raise ValidationError(
                _("Invalid action (%s, %s).") % (
                    self.direction, self.model))

    def get_action_id(self, name):
        """ Returns the id of the action given its name. """
        action_id = self.search([('name', '=', name)], limit=1)
        if action_id:
            return action_id.id
        return False
