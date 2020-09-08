from openupgradelib import openupgrade
from datetime import date


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    revisions = env["partner.communication.revision"].search([])
    for revision in revisions:
        revision.active_revision_id = env["partner.communication.revision.history"]\
            .create({
                "revision_number": revision.revision_number,
                "revision_date": revision.revision_date or date.today(),
                "subject": revision.subject,
                "body_html": revision.body_html,
                "linked_revision_id": revision.id,
                "proposition_text": revision.proposition_text,
                "raw_subject": revision.raw_subject,
            })
