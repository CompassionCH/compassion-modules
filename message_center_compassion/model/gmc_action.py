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
from openerp.exceptions import ValidationError


class gmc_action(models.Model):
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

    direction = fields.Selection(
        [('in', _('Incoming Message')), ('out', _('Outgoing Message'))],
        'Message Direction', required=True)
    name = fields.Char('GMC Message', size=20, required=True)
    model = fields.Char('OSV Model', size=30)
    type = fields.Selection('_get_message_types', 'Action Type',
                            required=True)
    description = fields.Text('Action to execute')

    def _get_message_types(self):
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

    @api.one
    @api.constrains('model', 'direction', 'action_type')
    def _validate_action(self):
        """ Test if the action can be performed on given model. """
        valid = False
        if self.direction == 'in':
            model_obj = self.env[self.model]
            valid = hasattr(model_obj, self.type)
        elif self.direction == 'out':
            valid = True

        if not valid:
            raise ValidationError(
                _("Invalid action (%s, %s, %s).") % (
                    self.direction, self.model, self.action_type))

    def get_action_id(self, name):
        """ Returns the id of the action given its name. """
        action_id = self.search([('name', '=', name)], limit=1)
        if action_id:
            return action_id.id
        return False
