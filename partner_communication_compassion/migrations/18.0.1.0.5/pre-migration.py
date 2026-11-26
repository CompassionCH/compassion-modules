from openupgradelib import openupgrade

XMLID_MODULE = "partner_communication_compassion"
# Module only installed in the Swiss databases (Nordic shares this code but has its
# own texts, which must not be overwritten)
SWISS_MODULE = "partner_communication_switzerland"
XMLID_NAME = "final_letter"
TEMPLATE_NAME = "B2S Final Letter"


@openupgrade.migrate()
def migrate(env, version):
    """The B2S Final Letter e-mail only existed in the databases (imported, without
    xmlid) while the config pointed to the New letter template in the data files.
    The template is now declared in the data files as ``final_letter``: link the
    existing record to this xmlid, otherwise the update would create a duplicate.
    The texts of the corrected templates are reloaded in the post-migration.
    Only done for the Swiss databases: Nordic uses other texts.
    """
    if not _is_swiss_database(env):
        return
    _link_final_letter(env)


def _is_swiss_database(env):
    env.cr.execute(
        "SELECT 1 FROM ir_module_module "
        "WHERE name = %s AND state IN ('installed', 'to upgrade')",
        (SWISS_MODULE,),
    )
    return bool(env.cr.fetchone())


def _link_final_letter(env):
    if env.ref(f"{XMLID_MODULE}.{XMLID_NAME}", raise_if_not_found=False):
        return
    # Prefer the template the final letter config already uses
    env.cr.execute(
        """
        SELECT t.id
        FROM mail_template t
        JOIN ir_model m ON m.id = t.model_id
        LEFT JOIN partner_communication_config c ON c.email_template_id = t.id
        WHERE m.model = 'partner.communication.job'
          AND t.name->>'en_US' = %s
        ORDER BY (c.id IS NULL), t.id
        LIMIT 1
        """,
        (TEMPLATE_NAME,),
    )
    row = env.cr.fetchone()
    if row:
        openupgrade.add_xmlid(
            env.cr,
            XMLID_MODULE,
            XMLID_NAME,
            "mail.template",
            row[0],
            noupdate=True,
        )
