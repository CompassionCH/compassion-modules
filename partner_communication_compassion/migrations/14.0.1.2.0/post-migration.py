from datetime import datetime

from dateutil.relativedelta import relativedelta
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE recurring_contract
        SET exit_communication_sent = COALESCE (sds_state_date, end_date, write_date)
        WHERE state = 'terminated'
        AND (end_date IS NULL OR end_date <= CURRENT_DATE - INTERVAL '6 months')
        """,
    )
    six_month_ago = datetime.today() - relativedelta(months=6)
    terminated_sponsorships = env["recurring.contract"].search(
        [
            ("state", "=", "terminated"),
            ("end_date", ">", six_month_ago),
        ]
    )
    exit_configs = env.ref(
        "partner_communication_compassion.lifecycle_child_planned_exit"
    ) + env.ref("partner_communication_compassion.lifecycle_child_unplanned_exit")
    for contract in terminated_sponsorships:
        exit_dates = env["partner.communication.job"].search_read(
            [
                ("config_id", "in", exit_configs.ids),
                ("state", "=", "done"),
                ("sent_date", "!=", False),
                (
                    "partner_id",
                    "in",
                    (contract.partner_id + contract.correspondent_id).ids,
                ),
                ("object_ids", "like", contract.id),
            ],
            ["sent_date"],
        )
        if exit_dates:
            contract.exit_communication_sent = max(r["sent_date"] for r in exit_dates)
