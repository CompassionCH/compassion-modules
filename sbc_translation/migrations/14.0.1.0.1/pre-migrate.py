from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.delete_records_safely_by_xml_id(env, [
        'sbc_translation.translation_comments_update',
        'sbc_translation.comments_reply',
        'sbc_translation.translation_issue_log',
    ])