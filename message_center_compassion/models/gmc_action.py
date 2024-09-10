##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _, api, fields, models
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

    _name = "gmc.action"
    _description = "GMC Action"

    name = fields.Char("GMC name", required=True)
    direction = fields.Selection(
        [("in", _("Incoming Message")), ("out", _("Outgoing Message"))],
        "Message Direction",
        required=True,
        index=True,
    )
    description = fields.Text("Action to execute")
    mapping_id = fields.Many2one(
        "compassion.mapping", "Mapping", required=True, index=True, readonly=False
    )
    model = fields.Char(related="mapping_id.model_id.model", readonly=True)
    connect_service = fields.Char(help="URL endpoint for sending messages to GMC")
    connect_outgoing_wrapper = fields.Char(
        help="Tag in which multiple messages can be encapsulated"
    )
    connect_answer_wrapper = fields.Char(
        help="Tag in which answer is found (for outgoing messages)"
    )
    success_method = fields.Char(
        default="write",
        help="method to call on the object upon success delivery "
        "(will pass the received answer as parameter as dictionary)",
    )
    failure_method = fields.Char(
        help="method called on the object when the response contain error"
    )

    incoming_method = fields.Char(
        default="process_commkit",
        help="method called on the object when receiving incoming message "
        "(will pass the received json as parameter as dictionary)",
    )
    batch_send = fields.Boolean(
        help="True if multiple objects can be sent through a single message"
    )
    auto_process = fields.Boolean(
        help="Set to True for processing the message as soon as it is created."
    )
    request_type = fields.Selection(
        [
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
        ]
    )
    no_outgoing_data = fields.Boolean(help="Put to true to force sending empty message")
    priority = fields.Integer(
        help="Define the priority at which the messages associated with this action "
        "will be treated. The more you're close to one the faster it will be "
        "proceeded.",
        default=100,
    )

    def write(self, vals):
        # prevent writing direction which should not be changed and is performance heavy
        vals.pop("direction", False)
        return super().write(vals)

    @api.constrains(
        "mapping_id", "direction", "incoming_method", "success_method", "failure_method"
    )
    def _validate_action(self):
        """Test if the action can be performed on given model."""
        for action in self:
            valid = True
            model_obj = self.env[action.mapping_id.model_id.model]
            if action.direction == "in":
                valid = hasattr(model_obj, action.incoming_method)
            else:
                valid = hasattr(model_obj, action.success_method)
                if action.failure_method:
                    valid &= hasattr(model_obj, action.failure_method)

            if not valid:
                raise ValidationError(
                    _("Invalid action (%s, %s).") % (action.direction, action.model)
                )
