import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """
    Careful! Install sbc_translation before performing this module update.
    """
    if not version:
        return

    env.cr.execute("""
    UPDATE correspondence c
    SET user_id = (
        SELECT id FROM res_users
        WHERE partner_id = c.translator_id
        LIMIT 1)
    WHERE translator_id IS NOT NULL;
    """)
    openupgrade.update_module_moved_fields(
        env.cr, "correspondence", ["translate_date"], "sbc_compassion", "sbc_translation")
