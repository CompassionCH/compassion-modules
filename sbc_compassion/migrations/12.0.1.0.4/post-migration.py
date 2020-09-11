from openupgradelib import openupgrade


def _update_reading_language(cr, sponsorship_id, lang):
    cr.execute(
        "UPDATE recurring_contract "
        "SET reading_language = %s "
        "WHERE id = %s", [lang, sponsorship_id]
    )


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    sponsorships_to_fill = env["recurring.contract"].search([
        ("reading_language", "=", False),
        ("child_id", "!=", False),
        ("state", "not in", ["terminated", "cancelled"])
    ])

    message_obj = env["gmc.message"]
    action_id = env.ref("sponsorship_compassion.create_sponsorship").id

    for sponsorship in sponsorships_to_fill:
        correspondent_lang_id = False
        for lang in sponsorship.correspondent_id.spoken_lang_ids:
            if sponsorship.child_id.correspondence_language_id.id == lang.id:
                _update_reading_language(
                    env.cr,
                    sponsorship.id,
                    lang.id
                )
                continue
            if sponsorship.correspondent_id.lang == lang.lang_id.code:
                correspondent_lang_id = lang.id
        if not sponsorship.reading_language and correspondent_lang_id:
            _update_reading_language(
                env.cr,
                sponsorship.id,
                correspondent_lang_id
            )

        if correspondent_lang_id:
            message_obj.create({
                "partner_id": sponsorship.correspondent_id.id,
                "child_id": sponsorship.child_id.id,
                "action_id": action_id,
                "object_id": sponsorship.id,
            }).process_messages()
