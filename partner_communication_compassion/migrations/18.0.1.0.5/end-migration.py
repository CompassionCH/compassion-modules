import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Catch up the biennials missed because of the picture dates (T3178).

    The first picture of a child was dated with its download day instead of
    its photo date, so a real new photo received less than six months after
    the child was fetched was not seen as a new one. Date those pictures with
    their publish date, then prepare the biennials that are still due.
    End migration: the communications need the country modules loaded (their
    templates and fields, e.g. the company commercial name).
    """
    # Only the pictures dated with their download day, published well before.
    env.cr.execute(
        r"""
        UPDATE compassion_child_pictures p
        SET date = published.date
        FROM (
            SELECT id, to_timestamp(
                substring(image_url FROM '/v(\d{9,11})/')::bigint
            )::date AS date
            FROM compassion_child_pictures
            WHERE image_url ~ '/v\d{9,11}/'
        ) published
        WHERE published.id = p.id
          AND p.date = p.create_date::date
          AND published.date < p.date - INTERVAL '30 days'
        RETURNING p.child_id
        """
    )
    rows = env.cr.fetchall()
    child_ids = {row[0] for row in rows}
    _logger.info(
        "T3178: %s pictures of %s children dated with their publish date",
        len(rows),
        len(child_ids),
    )

    # Prepared but not sent: staff review them before they reach the sponsors.
    children = env["compassion.child"].browse(child_ids)
    jobs_before = env["partner.communication.job"].search_count([])
    children.with_context(default_auto_send=False)._check_new_photo()
    _logger.info(
        "T3178: %s missed biennial communications prepared",
        env["partner.communication.job"].search_count([]) - jobs_before,
    )
