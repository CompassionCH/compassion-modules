##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import api, fields, models
from odoo.tools import relativedelta

_logger = logging.getLogger(__name__)


class ProjectCompassion(models.Model):
    _inherit = "compassion.project"

    sponsorships_count = fields.Integer(
        compute="_compute_sponsorships_count", store=True
    )

    contract_ids = fields.One2many(
        "recurring.contract", inverse_name="project_id", readonly=True
    )

    @api.depends("contract_ids.project_id")
    @api.depends("contract_ids.state")
    def _compute_sponsorships_count(self):
        for project in self:
            project.sponsorships_count = self.search_count(
                [
                    ("contract_ids.project_id", "=", project.id),
                    ("contract_ids.state", "not in", ["cancelled", "terminated"]),
                ]
            )

    def open_sponsorships(self):
        contract_list = self.env["recurring.contract"].search(
            [("child_id.project_id", "=", self.id)]
        )

        return {
            "type": "ir.actions.act_window",
            "name": "Sponsorships",
            "view_mode": "tree,form",
            "res_model": "recurring.contract",
            "domain": [("id", "in", contract_list.ids)],
            "target": "current",
            "context": self.env.context,
        }

    def hold_gifts_action(self):
        contracts = self.env["recurring.contract"].search(
            [
                ("child_code", "like", self.fcp_id),
                ("state", "in", ("active", "waiting", "mandate")),
            ]
        )
        contracts.hold_gifts()

    def reactivate_gifts(self):
        contracts = self.env["recurring.contract"].search(
            [
                ("child_code", "like", self.fcp_id),
                ("state", "in", ("active", "waiting", "mandate")),
            ]
        )
        contracts.reactivate_gifts()

    def sync_projects_from_gmc(
        self, requests_throttle_seconds=1.0, max_projects_to_sync=None
    ):
        """
        Synchronises the information and lifecycle events for all the projects with
        active sponsorships from the GMC. This should be called from a cron job and can
        take a long time to execute (a few hours). The reason for this is that the
        requests to the GMC server are delayed in order to avoid overwhelming their
        infrastructure.

        Args:
            requests_throttle_seconds (float, optional): Time to wait between requests,
                in seconds. This prevents the GMC server from being overwhelmed.
                Defaults to 1.0.
            max_projects_to_sync (int, optional): Maximum number of projects to sync.
                Used for testing. Defaults to None, which means: sync everything.
        """
        one_month_ago = fields.Date.today() - relativedelta(days=30)
        projects_to_sync = self.search(
            [
                ("status", "in", ["Active", "Suspended"]),
                ("last_update_date", "<", one_month_ago),
                ("sponsorships_count", ">", 0),
            ],
            limit=max_projects_to_sync,
        )
        nb_projects_to_sync = len(projects_to_sync)

        _logger.info(
            f"Starting projects sync from GMC. {projects_to_sync=}, "
            f"Estimated duration: "
            f"{requests_throttle_seconds * nb_projects_to_sync} seconds."
        )
        for i, p in enumerate(projects_to_sync):
            # Only synchronise projects for which we have sponsorships to speedup
            # execution and decrease remote server load
            p.with_delay(
                eta=requests_throttle_seconds * i,
                priority=500,
                channel="root.gmc_pool",
                description="Sync project from GMC",
            )._sync_from_gmc()

    def _sync_from_gmc(self):
        self.ensure_one()
        self.with_context(queue_job__no_delay=True).update_informations()
        self.with_context(queue_job__no_delay=True).get_lifecycle_event()
