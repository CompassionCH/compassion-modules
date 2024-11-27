import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr

    # Remove the column translator_id which has been deleted from the code in 2022
    cr.execute(
        """
        ALTER TABLE correspondence
            DROP COLUMN IF EXISTS translator_id;
        """
    )

    # Remove the column translator which is unused from 2016
    cr.execute(
        """
        ALTER TABLE correspondence
            DROP COLUMN IF EXISTS translator;
        """
    )
