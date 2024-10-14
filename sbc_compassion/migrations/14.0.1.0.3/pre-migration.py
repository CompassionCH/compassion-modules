import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    cr.execute(
        """
        SELECT DISTINCT(id) FROM res_partner 
        WHERE translation_user_id IS NULL 
        AND id IN (
            SELECT DISTINCT(translator_id) FROM correspondence c
            WHERE c.translator_id IS NOT NULL
            AND c.new_translator_id IS NOT NULL
        );
    """
    )
    # Fetch res_partners id with missing direct link to translation_user.
    partner_ids = [r[0] for r in cr.fetchall()]
    all_missing_links_resolved = True
    for r in partner_ids:
        # compute the direct link to translation_user by the correspondence table
        cr.execute(
            """
            SELECT DISTINCT(new_translator_id) FROM correspondence
            WHERE translator_id = %s;
        """ % r
        )
        translation_user_ids = [r[0] for r in cr.fetchall()]
        if len(translation_user_ids) == 0:
            _logger.info("Partner link to translation_user not found for id = %s" % r)
            all_missing_links_resolved = False
        elif len(translation_user_ids) > 1:
            _logger.info("Partner link to translation_user is not unique for id = %s"
                         % r)
            all_missing_links_resolved = False
        else:
            # set the direct link to res_partner -> translation_user
            link = translation_user_ids[0]
            openupgrade.logged_query(
                env.cr,
                """
                UPDATE res_partner
                SET translation_user_id = %s
                WHERE id = %s;
                """ % (link, r),
            )
    if all_missing_links_resolved:
        # Remove the redundant column translator_id
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

