# Copyright 2023 Emanuel Cino
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, SUPERUSER_ID
from openupgradelib import openupgrade


def pre_init_hook(cr):
    """Loaded before installing the module.

    None of this module's DB modifications will be available yet.

    If you plan to raise an exception to abort install, put all code inside a
    ``with cr.savepoint():`` block to avoid broken databases.

    :param odoo.sql_db.Cursor cr:
        Database cursor.
    """
    # This will avoid computing all values at module installation, which takes forever.
    env = api.Environment(cr, SUPERUSER_ID, {})
    openupgrade.add_fields(env, [(
        "event_id", "account.move.line", False, "integer", "integer", "crm_compassion"
    )])
