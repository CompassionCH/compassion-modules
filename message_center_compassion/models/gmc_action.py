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


class GmcAction(models.Model):
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
    description = fields.Text('Action to execute')
    connect_service = fields.Char()
    auto_process = fields.Boolean()
    request_type = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
    ])

    @api.one
    @api.constrains('model', 'direction')
    def _validate_action(self):
        """ Test if the action can be performed on given model. """
        valid = False
        if self.direction == 'in':
            model_obj = self.env[self.model]
            valid = hasattr(model_obj, 'process_commkit')
        elif self.direction == 'out':
            valid = True

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
