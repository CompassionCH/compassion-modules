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
    # Only the pictures dated with their download day, published before.
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
          AND published.date < p.date
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

    # Skip the children already in a biennial since their last picture came,
    # so that the sponsor does not receive the same picture twice.
    biennial = env.ref("partner_communication_compassion.biennial")
    # The biennial jobs are split once into one row per child, so that the
    # children are matched with an equality join instead of scanning the
    # object_ids of every job for each picture.
    env.cr.execute(
        r"""
        WITH biennial_child AS (
            SELECT DISTINCT job.create_date, child.id::integer AS child_id
            FROM partner_communication_job job,
                 unnest(string_to_array(job.object_ids, ',')) AS child(id)
            WHERE job.config_id = %s
              AND job.state != 'cancel'
              AND child.id ~ '^\d+$'
        )
        SELECT DISTINCT pic.child_id
        FROM (
            SELECT DISTINCT ON (child_id) id, child_id, create_date
            FROM compassion_child_pictures
            WHERE child_id = ANY(%s)
            ORDER BY child_id, date DESC, id DESC
        ) pic
        JOIN biennial_child bc
          ON bc.child_id = pic.child_id
         AND bc.create_date >= pic.create_date
        """,
        (biennial.id, list(child_ids)),
    )
    already_prepared = {row[0] for row in env.cr.fetchall()}
    _logger.info(
        "T3178: %s children skipped, already in a biennial", len(already_prepared)
    )

    # Prepared but not sent: staff review them before they reach the sponsors.
    # They are only merged into pending jobs that would not be sent either.
    # Generating a communication is slow (the report is rendered), so it is
    # done in queue jobs rather than in the migration.
    children = env["compassion.child"].browse(sorted(child_ids - already_prepared))
    children.with_context(
        default_auto_send=False, same_job_search=[("auto_send", "=", False)]
    ).with_delay_sh(
        "_check_new_photo",
        split=50,
        channel="root.partner_communication",
        priority=500,
    )
    _logger.info(
        "T3178: biennial communications of %s children queued for generation",
        len(children),
    )
