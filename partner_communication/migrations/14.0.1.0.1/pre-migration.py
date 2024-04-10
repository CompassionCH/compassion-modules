# TODO T1245: maybe delete this file if a better solution is found or this TODO
def migrate(cr, version):
    cr.execute(
        """
        UPDATE mail_template
        SET user_signature = false
        WHERE user_signature = true
        AND body_html LIKE '%·signature%';
        """
    )

    cr.execute(
        """
            SELECT id, name, lang, body_html
            FROM mail_template
            WHERE name = 'Personalized email'
            AND lang = '${object.partner_id.lang}';
        """
    )
