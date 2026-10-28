import json
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

BATCH_SIZE = 50

ZIP_LIST = "[object.get_letters_zip_url()] if len(letter) &gt; 5 else "
ZIP_URL = "object.get_letters_zip_url() if len(letter) &gt; 5 else "
URLS = "list(dict.fromkeys(letter.filtered({q}read_url{q}).mapped({q}read_url{q})))"
FIRST_URL = "letter.filtered({q}read_url{q})[:1].read_url"


@openupgrade.migrate()
def migrate(env, version):
    # T3559: above 5 letters, the e-mail links the zip of all letters. The template
    # is noupdate: patch only the link expressions, in every language.
    template = env.ref("partner_communication_compassion.new_letter", False)
    if template:
        env.cr.execute(
            "SELECT body_html FROM mail_template WHERE id = %s", [template.id]
        )
        bodies = env.cr.fetchone()[0]
        for lang, body in bodies.items():
            if "get_letters_zip_url" in body:
                continue
            for q in ("'", "&#x27;"):
                urls, first_url = URLS.format(q=q), FIRST_URL.format(q=q)
                body = body.replace(urls, ZIP_LIST + urls)
                body = body.replace(first_url, ZIP_URL + first_url)
            bodies[lang] = body
        env.cr.execute(
            "UPDATE mail_template SET body_html = %s WHERE id = %s",
            [json.dumps(bodies), template.id],
        )
    _fix_letter_formats(env)


def _fix_letter_formats(env):
    """
    Letters zipped in v14 kept letter_format 'zip' when the zip field was dropped.
    Recomputing the fields would read every scan from the filestore in full (the
    compute only needs the first bytes), which takes hours on a remote filestore.
    The type of the file is already stored in its attachment: use it in SQL, and
    queue the few letters whose attachment type is not conclusive.
    """
    cr = env.cr
    # The file name only differs by its extension
    cr.execute(
        r"""
        UPDATE correspondence c
        SET letter_format = 'pdf',
            file_name = regexp_replace(c.file_name, '\.zip$', '.pdf')
        FROM ir_attachment a
        WHERE c.letter_format = 'zip'
            AND a.res_model = 'correspondence'
            AND a.res_field = 'sponsor_letter_scan'
            AND a.res_id = c.id
            AND a.mimetype = 'application/pdf'
        """
    )
    _logger.info("%s letters are pdf files", cr.rowcount)
    # Without scan, the computed format is empty
    cr.execute(
        r"""
        UPDATE correspondence c
        SET letter_format = NULL,
            file_name = regexp_replace(c.file_name, '\.zip$', '.pdf')
        WHERE c.letter_format = 'zip'
            AND NOT EXISTS (
                SELECT 1 FROM ir_attachment a
                WHERE a.res_model = 'correspondence'
                    AND a.res_field = 'sponsor_letter_scan'
                    AND a.res_id = c.id
            )
        """
    )
    _logger.info("%s letters have no scan", cr.rowcount)
    # Real zip files keep their format. Other types: check the file in a job
    cr.execute(
        """
        SELECT c.id FROM correspondence c
        JOIN ir_attachment a ON a.res_model = 'correspondence'
            AND a.res_field = 'sponsor_letter_scan'
            AND a.res_id = c.id
        WHERE c.letter_format = 'zip'
            AND COALESCE(a.mimetype, '') != 'application/zip'
        """
    )
    unclear = env["correspondence"].browse([row[0] for row in cr.fetchall()])
    _logger.info("%s letters to check in queue jobs", len(unclear))
    if unclear:
        unclear.with_delay_sh(
            "_refresh_letter_format",
            channel="root.sbc_migration",
            priority=500,
            split=BATCH_SIZE,
            description="Refresh the format of letters zipped in v14",
        )
