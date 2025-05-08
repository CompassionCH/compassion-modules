from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    openupgrade.add_fields(
        env,
        [
            (
                "email_from",
                "partner.communication.job",
                "partner_communication_job",
                "char",
                False,
                "partner_communication",
            ),
            (
                "reply_to",
                "partner.communication.job",
                "partner_communication_job",
                "char",
                False,
                "partner_communication",
            ),
        ],
    )
