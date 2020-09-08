def migrate(cr, version):
    if not version:
        return

    revisions = cr.env["partner.communication.revision"].search([])
    for revision in revisions:
        cr.env["partner.communication.revision.history"].create({
            "revision_number": revision.revision_number,
            "revision_date": revision.revision_date,
            "lang": revision.lang,
            "subject": revision.subject,
            "simplified_text": revision.simplified_text,
            "body_html": revision.body_html,
            "linked_revision_id": revision.id,
        })
