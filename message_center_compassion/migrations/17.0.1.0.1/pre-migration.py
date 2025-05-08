from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    openupgrade.delete_records_safely_by_xml_id(
        env,
        [
            "message_center_compassion.notification_settings",
            "message_center_compassion.gmc_settings",
        ],
        True,
    )
