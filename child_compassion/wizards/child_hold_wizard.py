##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Philippe Heer
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import tools, models, api, fields, _

testing = tools.config.get("test_enable")
_logger = logging.getLogger(__name__)


class ChildHoldWizard(models.TransientModel):
    _name = "child.hold.wizard"
    _inherit = "compassion.abstract.hold"

    return_action = fields.Selection(
        [
            ("view_children", "View Children"),
            ("view_holds", "View Holds"),
            ("search", "Search for other children"),
        ],
        required=True,
        default="view_children",
    )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def get_hold_values(self):
        hold_vals = super().get_hold_values()
        if self.channel in ("ambassador", "event"):
            hold_vals["secondary_owner"] = self.ambassador.name
        return hold_vals

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def send(self):
        holds = self.env["compassion.hold"]
        child_search = (
            self.env["compassion.childpool.search"]
                .browse(self.env.context.get("active_id"))
                .global_child_ids
        )
        chunk_size = 10
        for i in range(0, len(child_search), chunk_size):
            _logger.info(f"Processing chunk {i} for sending hold requests")
            try:
                messages = self.env["gmc.message"]
                for child in child_search[i: i + chunk_size]:
                    # Save children form global children to compassion children
                    child_comp = self.env["compassion.child"].create(
                        child.get_child_vals()
                    )

                    # Create Holds for children to reserve
                    hold_vals = self.get_hold_values()
                    hold_vals["child_id"] = child_comp.id
                    hold = holds.create(hold_vals)
                    holds += hold

                    # Create messages to send to Connect
                    action_id = self.env.ref("child_compassion.create_hold").id

                    messages += messages.create(
                        {"action_id": action_id, "object_id": hold.id}
                    )
                messages.process_messages()
                if not testing:
                    self.env.cr.commit()  # pylint: disable=invalid-commit
            except:
                _logger.error("Hold chunk failed", exc_info=True)
                self.env.cr.rollback()

        return self._get_action(holds)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_action(self, holds):
        """ Returns the action after closing the wizard. """
        action = {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "context": self.env.context,
            "target": "current",
        }
        if self.return_action == "view_children":
            action.update(
                {
                    "name": _("Children on hold"),
                    "domain": [("id", "in", holds.mapped("child_id").ids)],
                    "res_model": "compassion.child",
                }
            )
        elif self.return_action == "view_holds":
            action.update(
                {
                    "name": _("Created holds"),
                    "domain": [("id", "in", holds.ids)],
                    "res_model": "compassion.hold",
                }
            )
        elif self.return_action == "search":
            action = True

        return action
