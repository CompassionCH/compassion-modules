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

    openupgrade.update_module_moved_fields(
        env.cr, "correspondence", ["translate_date"], "sbc_compassion", "sbc_translation")
