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

    # Update all correspondence texts that are not yet published (the others can be manually corrected as needed)
    correspondence = env["correspondence"].search([(
        "state", "not in", ["Published to Global Partner", "Printed and sent to ICP", "Exception",
                            "Quality check unsuccessful"]
    )])
    correspondence.create_text_boxes()

    # Update translation done
    env.cr.execute("""
        UPDATE correspondence SET translate_done = translate_date
        WHERE translate_date IS NOT NULL;
        UPDATE correspondence SET translate_date = write_date
        WHERE state = 'Global Partner translation queue'
        AND translate_date IS NULL;
    """)
