##############################################################################
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import json
import logging
import re
import traceback
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools.onramp_connector import OnrampConnector

logger = logging.getLogger(__name__)


class GmcMessage(models.Model):
    """Pool of messages exchanged between Compassion CH and GMC."""

    _name = "gmc.message"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Connect Message"

    _order = "date desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(related="action_id.name", readonly=True)
    description = fields.Text(
        "Action to execute", related="action_id.description", readonly=True
    )
    direction = fields.Selection(
        related="action_id.direction", store=True, readonly=True
    )
    object_id = fields.Integer("Resource")
    object_ids = fields.Char(
        "Related records",
        help="Used for incoming messages containing "
        "several records. (ids separated by commas)",
    )
    res_name = fields.Char(compute="_compute_res_name", store=True)
    partner_id = fields.Many2one("res.partner", "Partner")

    request_id = fields.Char("Request ID")
    date = fields.Datetime(
        "Message Date", required=True, default=fields.Datetime.now, index=True
    )
    action_id = fields.Many2one(
        "gmc.action", "GMC Message", ondelete="restrict", required=False
    )
    process_date = fields.Datetime(tracking=True)
    state = fields.Selection(
        [
            ("new", _("New")),
            ("pending", _("Pending")),
            ("postponed", _("Postponed")),
            ("success", _("Success")),
            ("failure", _("Failure")),
            ("odoo_failure", _("Odoo Failure")),
        ],
        "State",
        default="new",
        tracking=True,
        index=True,
    )
    failure_reason = fields.Text("Failure details", tracking=True)
    headers = fields.Text()
    content = fields.Text()
    answer = fields.Text()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends("object_id", "action_id")
    def _compute_res_name(self):
        for message in self:
            try:
                res_object = self.env[message.action_id.model].browse(message.object_id)
                if res_object:
                    message.res_name = res_object.display_name
            except KeyError:
                message.res_name = "Unknown"

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        message = False
        if "object_id" in vals:
            message = self.search(
                [
                    ("object_id", "=", vals["object_id"]),
                    ("state", "in", ("new", "pending")),
                    ("action_id", "=", vals["action_id"]),
                ]
            )

        if not message:
            message = super().create(vals)

        if message.action_id.auto_process:
            message.process_messages()
        return message

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    def update_res_name(self):
        self._compute_res_name()

    def process_messages(self):
        new_messages = self.filtered(lambda m: m.state not in ("postponed", "success"))
        new_messages.write({"state": "pending", "failure_reason": False})
        if self.env.context.get("async_mode", True):
            # We define the priority with the first message because we're supposed
            # to have only one actions by messages group
            new_messages.with_delay(
                priority=self[0].action_id.priority
            )._process_messages()
        else:
            new_messages._process_messages()
        return True

    def get_answer_dict(self, index=0):
        answer = json.loads(self[index].answer)
        if isinstance(answer, list):
            answer = answer[index]
        return answer

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def force_success(self):
        self.write({"state": "success", "failure_reason": False})
        self.mapped("message_ids").unlink()
        return True

    def reset_message(self):
        self.write(
            {
                "state": "new",
                "process_date": False,
                "failure_reason": False,
                "answer": False,
                "request_id": False,
            }
        )
        return True

    def open_related(self):
        self.ensure_one()
        if self.direction == "out":
            # Outgoing messages are always related to one object.
            return {
                "name": "Related object",
                "type": "ir.actions.act_window",
                "res_model": self.action_id.model,
                "res_id": self.object_id,
                "view_mode": "form",
            }
        else:
            # Incoming messages can be related to several objects.
            res_ids = self.object_ids.split(",")
            return {
                "name": "Related object",
                "type": "ir.actions.act_window",
                "res_model": self.action_id.model,
                "domain": [("id", "in", res_ids)],
                "view_mode": "tree,form",
            }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _process_messages(self):
        """Process given messages in pool."""
        today = datetime.now()
        messages = self.filtered(lambda mess: mess.state == "pending")
        if not self.env.context.get("force_send"):
            messages = messages.filtered(lambda mess: mess.date <= today)

        # Verify all messages have the same action (cannot execute multiple
        # actions at once) If this is modified we should adapt the call of this method
        action = messages.mapped("action_id")
        if len(action) > 1:
            raise UserError(
                _(
                    "Cannot process several actions at the same "
                    "time. Please process each message type "
                    "individually."
                )
            )
        elif not action:
            # No messages pending
            return True

        message_update = {"process_date": fields.Datetime.now()}
        if action.direction == "in":
            try:
                message_update.update(self._perform_incoming_action())
            except Exception:
                # Abort pending operations
                logger.error("Failure when processing message", exc_info=True)
                self.env.cr.rollback()
                self.env.clear()
                # Write error
                message_update.update(
                    {"state": "failure", "failure_reason": traceback.format_exc()}
                )

        elif action.direction == "out":
            self._perform_outgoing_action()
        else:
            raise NotImplementedError

        self.write(message_update)
        if message_update.get("state") == "success":
            # Remove thread history
            self.mapped("message_ids").unlink()

        return True

    def _perform_incoming_action(self):
        """Convert the data incoming from Connect into Odoo object values
        and call the process_commkit method on the related object."""
        object_ids = list()
        action = self.mapped("action_id")
        for message in self:
            model_obj = self.env[action.model]
            commkit_data = [json.loads(message.content)]

            object_ids.extend(
                map(str, getattr(model_obj, action.incoming_method)(*commkit_data))
            )

        return {
            "state": "success" if object_ids else "failure",
            "object_ids": ",".join(object_ids),
            "failure_reason": "No related objects found." if not object_ids else False,
        }

    def _perform_outgoing_action(self):
        """Send a message to Compassion Connect"""
        # Load objects
        action = self.mapped("action_id")
        data_objects = (
            self.env[action.model]
            .with_context(lang="en_US")
            .browse(self.mapped("object_id"))
        )

        # Replay answer if message was already sent and received success
        to_send = self
        for i, message in enumerate(self):
            if message.request_id:
                answer_data = json.loads(message.answer)
                message._process_single_answer(data_objects[i], answer_data)
                to_send -= message

        # Notify objects sent to connect for special handling if needed.
        data_objects = (
            self.env[action.model]
            .with_context(lang="en_US")
            .browse(to_send.mapped("object_id"))
        )
        if hasattr(data_objects, "on_send_to_connect"):
            data_objects.on_send_to_connect()

        message_data = {}
        if action.connect_outgoing_wrapper:
            # Object is wrapped in a tag. ("MessageTag": [objects_to_send])
            if action.batch_send:
                # Send multiple objects in a single message to GMC
                # make batch of 20 messages to avoid timeouts
                split = 20
                nb_batches = len(data_objects) // split
                remaining = (len(data_objects) % split) and 1
                for j in range(0, nb_batches + remaining):
                    i = j * split
                    message_data = {action.connect_outgoing_wrapper: list()}
                    for data_object in data_objects[i : i + split]:
                        if not action.no_outgoing_data:
                            message_data[action.connect_outgoing_wrapper].append(
                                data_object.data_to_json(action.mapping_id.name)
                            )
                        else:
                            message_data[action.connect_outgoing_wrapper].append({})
                    to_send[i : i + split]._send_message(message_data)
            else:
                # Send individual message for each object
                for i in range(0, len(data_objects)):
                    if not action.no_outgoing_data:
                        message_data[action.connect_outgoing_wrapper] = [
                            data_objects[i].data_to_json(action.mapping_id.name)
                        ]
                    else:
                        message_data[action.connect_outgoing_wrapper] = {}
                    to_send[i]._send_message(message_data)

        else:
            # Send individual message for each object without Wrapper
            for i in range(0, len(data_objects)):
                if not action.no_outgoing_data:
                    message_data = data_objects[i].data_to_json(action.mapping_id.name)
                to_send[i]._send_message(message_data)

    def _send_message(self, message_data):
        """Sends the prepared message and gets the answer from GMC."""
        action = self.mapped("action_id")
        onramp = OnrampConnector(self.env)
        url_endpoint = self._get_url_endpoint()
        if action.request_type == "GET":
            onramp_answer = onramp.send_message(
                url_endpoint, action.request_type, params=message_data
            )
        else:
            onramp_answer = onramp.send_message(
                url_endpoint, action.request_type, body=message_data
            )

        # Extract the Answer
        content_sent = message_data.get(action.connect_outgoing_wrapper, message_data)
        content_data = json.dumps(content_sent, indent=4, sort_keys=True)
        results = onramp_answer.get("content", {})
        answer_wrapper = action.connect_answer_wrapper
        try:
            if answer_wrapper:
                for wrapper in answer_wrapper.split("."):
                    results = results.get(wrapper, results)
        except (AttributeError, KeyError):
            logger.error("Unexpected answer: %s", results)
        if not results and onramp_answer.get("code") != 200:
            self._answer_failure(content_data, onramp_answer)
            return

        if not isinstance(results, list):
            results = [results]
        data_objects = (
            self.env[action.model]
            .with_context(lang="en_US")
            .browse(self.mapped("object_id"))
        )

        if 200 <= onramp_answer["code"] < 300:
            # Success, loop through answer to get individual results
            for i in range(0, len(results)):
                result = results[i]
                content_data = (
                    json.dumps(content_sent[i], indent=4, sort_keys=True)
                    if isinstance(content_sent, list)
                    else content_data
                )
                if isinstance(result, dict) and result.get("Code", 2000) == 2000:
                    # Individual message was successfully processed
                    # Commit state before processing the success
                    self[i].write(
                        {
                            "content": content_data,
                            "request_id": onramp_answer.get("request_id")
                            or str(self[i].id),
                            "answer": json.dumps(result, indent=4, sort_keys=True),
                            "state": "success",
                        }
                    )
                    self[i]._process_single_answer(data_objects[i], result)
                elif isinstance(result, dict):
                    if action.failure_method:
                        getattr(data_objects[i], action.failure_method)(result)
                    self[i].write(
                        {
                            "content": content_data,
                            "state": "failure",
                            "failure_reason": result["Message"],
                            "answer": json.dumps(result, indent=4, sort_keys=True),
                        }
                    )
                else:
                    # We got a simple string as result, nothing more to do
                    self[i].write(
                        {
                            "content": content_data,
                            "state": "success",
                            "answer": str(result),
                        }
                    )
        else:
            for i in range(0, len(results)):
                result = results[i]
                if action.failure_method:
                    getattr(data_objects[i], action.failure_method)(result)
                self.write(
                    {"content": json.dumps(content_sent, indent=4, sort_keys=True)}
                )
                self[i]._answer_failure(content_data, onramp_answer, result)

    def _process_single_answer(self, data_object, answer_data):
        """
        When processing outgoing messages, here we treat a single
        response for a message and execute the appropriate callback.
        :param data_object: the related object of the message
        :param answer_data: the json returned by GMC
        :return: None
        """
        self.ensure_one()
        action = self.action_id
        try:
            with self.env.cr.savepoint():
                answer_data = data_object.json_to_data(
                    answer_data, action.mapping_id.name
                )
                f = getattr(data_object, action.success_method)
                f(answer_data)
                self.state = "success"
        except Exception as e:
            logger.error(traceback.format_exc())
            try:
                if action.failure_method:
                    getattr(data_object, action.failure_method)(answer_data)
            except Exception:
                logger.warning("Failure method of message %s failed", [action.name])
            self.write(
                {
                    "state": "odoo_failure",
                    "failure_reason": str(e),
                }
            )

    def _answer_failure(self, content_data, onramp_answer, results=None):
        """Write error message when onramp answer is not a success.
        :onramp_answer: complete message received back
        :results: extracted content from the answer
        """
        error_code = onramp_answer.get("code", onramp_answer.get("Code"))
        if results and isinstance(results, list):
            error_message = "\n".join(map(lambda m: m.get("Message", ""), results))
        else:
            error_message = onramp_answer.get(
                "content", {"Error": onramp_answer.get("Error", "None")}
            )
        self.write(
            {
                "state": "failure",
                "failure_reason": f"[{error_code}] {error_message}",
                "answer": json.dumps(
                    results or onramp_answer, indent=4, sort_keys=True
                ),
                "content": content_data,
            }
        )

    def _get_url_endpoint(self):
        """Gets the endpoint of GMC based on the action."""
        url_endpoint = self.mapped("action_id").connect_service
        if "${object" in url_endpoint:
            url_endpoint = re.sub(
                r"\$\{(object\.)(.+?)\}",
                lambda match: self._replace_object_string(match),
                url_endpoint,
            )
        return url_endpoint

    def _replace_object_string(self, object_match):
        """Takes a string like ${object.field} and returns the field."""
        self.ensure_one()
        obj = self.env[self.action_id.model].browse(self.object_id)
        field_name = object_match.groups()[1]
        field_value = obj.mapped(field_name)[0]
        return str(field_value)

    def _validate_outgoing_action(self):
        """Inherit to add message validation before sending it."""
        return True

    @api.model
    def _needaction_domain_get(self):
        return [("state", "in", ("new", "pending"))]
