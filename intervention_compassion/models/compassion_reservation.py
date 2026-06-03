from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CompassionReservation(models.Model):
    _inherit = "compassion.reservation"

    reservation_type = fields.Selection(
        selection_add=[
            ("fcp_intervention", "FCP Intervention"),
        ],
        ondelete={"fcp_intervention": "cascade"},
    )
    service_level = fields.Integer("Service Level")
    intervention_ids = fields.One2many(
        "compassion.intervention", "compassion_reservation_id", "Interventions"
    )
    number_intervention_reserved = fields.Integer(compute="_compute_nb_interventions")

    @api.constrains("service_level")
    def _check_service_level(self):
        for reservation in self:
            if (
                reservation.reservation_type == "fcp_intervention"
                and reservation.service_level not in [1, 2, 3]
            ):
                raise ValidationError(
                    _(
                        "Service level must be between 1 and 3 for "
                        "FCP Intervention reservations."
                    )
                )

    def _compute_nb_interventions(self):
        for reservation in self:
            reservation.number_intervention_reserved = len(reservation.intervention_ids)

    def handle_reservation(self, cancel=False):
        messages = super().handle_reservation(cancel=cancel)
        for reservation in self:
            if reservation.reservation_type == "fcp_intervention":
                if cancel:
                    # TODO No valid action for this case??
                    action = self.env.ref(
                        "intervention_compassion.intervention_cancel_fcp_reservation_action"
                    )
                else:
                    if reservation.reservation_id:
                        action = self.env.ref(
                            "intervention_compassion.intervention_update_fcp_reservation_action"
                        )
                    else:
                        action = self.env.ref(
                            "intervention_compassion.intervention_create_fcp_reservation_action"
                        )
                # Those actions have auto_process enabled, no need process them manually
                messages += messages.create(
                    {
                        "action_id": action.id,
                        "object_id": reservation.id,
                        "child_id": reservation.child_id.id,
                    }
                )
        return messages

    def show_reserved_interventions(self):
        self.ensure_one()
        return {
            "name": _("Reserved Interventions"),
            "type": "ir.actions.act_window",
            "res_model": "compassion.intervention",
            "view_mode": "tree,form",
            "domain": [("compassion_reservation_id", "=", self.id)],
        }
