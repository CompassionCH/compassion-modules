from io import BytesIO

from lxml import etree
from openupgradelib import openupgrade

from odoo import tools

MODULE = "partner_communication_compassion"
# Module only installed in the Swiss databases (Nordic shares this code but has its
# own texts, which must not be overwritten)
SWISS_MODULE = "partner_communication_switzerland"
# Templates corrected in T3527, by data file
FIXED_TEMPLATES = {
    "data/child_letter_emails.xml": ["new_letter", "final_letter"],
    "data/depart_communications.xml": [
        "email_child_planned_exit",
        "email_child_unplanned_exit",
    ],
}


@openupgrade.migrate()
def migrate(env, version):
    """Reload the texts (subject, body and sender fields) of the templates corrected
    in T3527. The data files are noupdate, so the update skips existing records.
    Only done for the Swiss databases: Nordic uses other texts.
    """
    env.cr.execute(
        "SELECT 1 FROM ir_module_module "
        "WHERE name = %s AND state IN ('installed', 'to upgrade')",
        (SWISS_MODULE,),
    )
    if not env.cr.fetchone():
        return
    for filename, xmlids in FIXED_TEMPLATES.items():
        _reload_records(env, filename, xmlids)


def _reload_records(env, filename, xmlids):
    """Load only the given records of a data file, the other records of the file
    must keep their database values."""
    with tools.file_open(f"{MODULE}/{filename}", "rb") as fp:
        source = etree.parse(fp).getroot()
    selection = etree.Element("odoo", noupdate="1")
    selection.extend(r for r in source.iter("record") if r.get("id") in xmlids)
    assert len(selection) == len(xmlids), f"Missing records in {filename}"
    # Drop the translated values, they are loaded again from the .po files. Otherwise
    # the old translations are kept when the structure of the English text changed.
    env.cr.execute(
        """
        UPDATE mail_template t
        SET body_html = jsonb_build_object('en_US', t.body_html->>'en_US'),
            subject = jsonb_build_object('en_US', t.subject->>'en_US')
        FROM ir_model_data d
        WHERE d.model = 'mail.template' AND d.res_id = t.id
          AND d.module = %s AND d.name IN %s
        """,
        (MODULE, tuple(xmlids)),
    )
    stream = BytesIO(etree.tostring(selection))
    stream.name = filename
    # Mode init loads the records even if they exist and the file is noupdate
    tools.convert_xml_import(env, MODULE, stream, mode="init")
