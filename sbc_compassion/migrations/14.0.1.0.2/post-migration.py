from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if version:
        letters = env["correspondence"].search([("read_url", "=", False), ("uuid", "!=", False)])
        letters.with_delay()._compute_read_url()
