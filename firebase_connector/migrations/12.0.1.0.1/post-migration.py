from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return
    env.cr.execute("update firebase_notification set stage_id=4 where sent=True")
    openupgrade.load_xml(env.cr, 'firebase_connector', 'data/ir_cron.xml')
