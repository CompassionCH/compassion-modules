from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class CompassionProject(models.Model):
    """Send Communication when Hold Removal is received."""

    _inherit = "compassion.project"

    tpl_item_ids = fields.Many2many(
        "communication.snippet",
        string="Caption to use for pictures, or prayer shared by fcp, or else",
    )

    last_suspension_communication_date = fields.Date(
        string="Date of the last suspension communication",
        help="Records the date of the last suspension communication.",
    )

    def reactivate_project(self):
        """
        Inherit reactivation to trigger 'FCP Suspension Follow Up'
        """
        # 1. Execute original logic
        res = super().reactivate_project()

        # 2. Trigger the communication
        self._trigger_communication("project_suspension_follow_up")

        return res

    def _trigger_communication(self, config_xml_id):
        """
        Finds all active sponsors for children in the project and
        sends communication to the sponsor.
        """
        # 1. Get the communication configuration record
        comm_config = self.env.ref(f"partner_communication_compassion.{config_xml_id}")

        for project in self:
            # 2. Find all active sponsorships for children in this project
            contracts = self.env["recurring.contract"].search(
                [("child_id.project_id", "=", project.id), ("state", "=", "active")]
            )

            # 3. Send communication to each sponsor
            for contract in contracts:
                contract.with_context(
                    default_object_ids=contract.child_id.id
                ).send_communication(communication=comm_config, correspondent=True)

            # 4. Update the last suspension communication date
            project.last_suspension_communication_date = fields.Date.today()

    @api.model
    def _cron_suspension_communication(self):
        """
        Finds all projects suspended for more than 2 months without follow-up
        communication and triggers the appropriate communication.
        """
        today = fields.Date.today()
        two_months_ago = today - relativedelta(months=2)

        # Find projects suspended for > 2 months
        # AND (no follow-up yet OR last follow-up was > 2 months ago)
        projects = self.search(
            [
                ("suspension", "in", ["suspended", "fund-suspended"]),
                ("last_lifecycle_id.type", "=", "Suspension"),
                ("last_lifecycle_id.date", "<=", two_months_ago),
                "|",
                ("last_suspension_communication_date", "=", False),
                ("last_suspension_communication_date", "<=", two_months_ago),
            ]
        )

        for project in projects:
            last_lifecycle_date = project.last_lifecycle_id.date

            if (
                not project.last_suspension_communication_date
                or project.last_suspension_communication_date < last_lifecycle_date
            ):
                # 1. First time for this lifecycle event: Announcement
                project._trigger_communication("project_suspension")

            else:
                # 2. We already announced it, but 2 months have passed: Follow-up
                project._trigger_communication("project_suspension_follow_up")
