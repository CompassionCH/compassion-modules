from openupgradelib import openupgrade


def migrate(cr, version):
    cr.execute(
        """
            UPDATE mail_template
            SET lang = '${object.partner_id.lang}',
            body_html = body_html || '<div>
            % if user and user.signature:
                ${user.signature | safe}
            % endif
            </div>'
            WHERE model = 'crm.claim';
        """
    )
    cr.execute(
        """
        UPDATE ir_translation
        SET value = value || '<div>
         % if user and user.signature:
                ${user.signature | safe}
            % endif
            </div>'
        WHERE name = 'mail.template,body_html'
        AND res_id IN (SELECT id from mail_template WHERE model='crm.claim');
        """,
    )
    openupgrade.rename_xmlids(cr, [(
        "partner_communication_switzerland.email_template_default_communication",
        "partner_communication.default_communication_template")])
