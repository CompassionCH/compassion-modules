# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from ..tools.onramp_connector import OnrampConnector

from openerp import api, models, fields


class GmcMessage(models.Model):
    """ Add fields to store the content of the received message from Onramp.
    Handle new messages differently than messages destinated to old
    Onramp (before TCPT R3).

    New out messages are linked to objects that must implement these two
    methods and one field in order to work :

        def convert_for_connect():
            - returns a dictionary that will be the json content of the
              sent message (representing the object values).
        def get_connect_data(data):
            - if Compassion Connect returns some data, this method will be
              called in order to send back the data to the object.

    """
    _inherit = 'gmc.message.pool'

    headers = fields.Text()
    content = fields.Text()
    letter_id = fields.Many2one(
        'sponsorship.correspondence', 'Letter', compute='_set_letter_id',
        store=True)

    @api.depends('object_id')
    def _set_partner_id(self):
        for message in self:
            model = message.action_id.model
            if model == 'sponsorship.correspondence':
                letter = self.env[model].browse(message.object_id)
                message.partner_id = letter.correspondant_id.id
            else:
                super(GmcMessage, message)._set_partner_id()

    @api.depends('object_id')
    def _set_child_id(self):
        for message in self:
            model = message.action_id.model
            if model == 'sponsorship.correspondence':
                letter = self.env[model].browse(message.object_id)
                message.child_id = letter.child_id.id
            else:
                super(GmcMessage, message)._set_child_id()

    @api.depends('object_id')
    def _set_letter_id(self):
        for message in self:
            model = message.action_id.model
            if model == 'sponsorship.correspondence':
                message.letter_id = message.object_id

    def _perform_outgoing_action(self):
        """ If message is destinated to new Onramp, send them directly.
        Otherwise, use old method with middleware. """
        action = self.action_id
        result = False
        if action.connect_service:
            result = self._proccess_to_compassion_connect()
        else:
            result = super(GmcMessage, self)._perform_outgoing_action()
        return result

    def _proccess_to_compassion_connect(self):
        """ Send a message to Compassion Connect (new Onramp) """
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


class GmcAction(models.Model):
    """ Add fields to identify new actions that must be sent to the new
    ramp of Compassion Connect instead of the middleware.
    """
    _inherit = 'gmc.action'

    # Name of the service provided by Compassion Connect
    connect_service = fields.Char()
    request_type = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
    ])
