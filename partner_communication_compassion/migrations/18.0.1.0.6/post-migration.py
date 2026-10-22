import json

from openupgradelib import openupgrade

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
    # Letters zipped in v14 kept letter_format 'zip' when the zip field was dropped
    letters = env["correspondence"].search([("letter_format", "=", "zip")])
    for fname in ("letter_format", "file_name"):
        env.add_to_compute(letters._fields[fname], letters)
        letters.flush_recordset([fname])
