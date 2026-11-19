import json
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# T3274: found while investigating why sponsorship onboarding communications
# crashed - the "Donation - Thank You Letter" template had its ">"/"<"/'"'/"'"
# QWeb comparison/string-literal operators double-escaped
# (e.g. "&amp;gt;" instead of "&gt;"), so Odoo 18's stricter QWeb compiler
# tried to evaluate the still-escaped "&amp;gt;" text as a Python operator
# and crashed. This is a purely mechanical unescape, safe to apply to any
# mail_template regardless of which module (if any) owns it - many of the
# affected templates were created directly via the UI and have no owning
# module at all, so a per-module migration could never reach them.
ENTITY_FIXES = (
    ("&amp;gt;", "&gt;"),
    ("&amp;lt;", "&lt;"),
    ("&amp;quot;", "&quot;"),
    ("&amp;apos;", "&apos;"),
)


def _fix_body(body):
    if not body:
        return body
    for broken, fixed in ENTITY_FIXES:
        body = body.replace(broken, fixed)
    return body


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute(
        """
        SELECT id, body_html FROM mail_template
        WHERE body_html::text LIKE '%&amp;gt;%'
           OR body_html::text LIKE '%&amp;lt;%'
           OR body_html::text LIKE '%&amp;quot;%'
           OR body_html::text LIKE '%&amp;apos;%'
        """
    )
    rows = env.cr.fetchall()
    fixed_count = 0
    for template_id, body_html in rows:
        fixed = {lang: _fix_body(body) for lang, body in body_html.items()}
        if fixed != body_html:
            env.cr.execute(
                "UPDATE mail_template SET body_html = %s WHERE id = %s",
                (json.dumps(fixed), template_id),
            )
            fixed_count += 1
    _logger.info(
        "T3274: unescaped double-escaped &gt;/&lt;/&quot;/&apos; entities "
        "in %s/%s mail_template rows",
        fixed_count,
        len(rows),
    )
