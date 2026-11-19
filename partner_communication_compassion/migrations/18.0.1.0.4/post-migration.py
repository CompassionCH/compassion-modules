import json
import re

from openupgradelib import openupgrade

# The v14 -> v18 QWeb conversion skipped the last "% endif" of de_DE/fr_CH/it_IT
# (indented, no trailing newline): it stayed printed on the letter and left the
# enclosing <t t-else=""> unclosed. It is followed by </body> on the same line,
# so it has to be matched as a substring, not as a whole line.
STRAY_ENDIF_RE = re.compile(r"(?m)^[ \t]*%[ \t]*endif[ \t]*")


@openupgrade.migrate()
def migrate(env, version):
    template = env.ref("partner_communication_compassion.email_biennial")
    env.cr.execute("SELECT body_html FROM mail_template WHERE id = %s", (template.id,))
    (body_html,) = env.cr.fetchone()
    fixed = {
        lang: STRAY_ENDIF_RE.sub("</t>", body)
        for lang, body in (body_html or {}).items()
    }
    if fixed != body_html:
        env.cr.execute(
            "UPDATE mail_template SET body_html = %s WHERE id = %s",
            (json.dumps(fixed), template.id),
        )
