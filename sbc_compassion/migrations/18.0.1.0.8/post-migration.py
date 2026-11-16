import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # T3646: S10 letters printing their translation over page 2's printed text
    l1 = env.ref("sbc_compassion.b2s_l1")
    messages = env["gmc.message"].search([("content", "like", "-1S10-")])
    messages = messages.filtered(lambda m: m.action_id.model == "correspondence")
    letter_ids = [
        int(letter_id)
        for message in messages
        for letter_id in (message.object_ids or str(message.object_id)).split(",")
        if letter_id.strip().isdigit()
    ]
    letters = env["correspondence"].search(
        [("id", "in", letter_ids), ("template_id", "=", l1.id)]
    )
    letters = letters.filtered(
        lambda letter: any(
            len((paragraph.translated_text or "").strip()) >= 5
            for paragraph in letter.page_ids[1:2].paragraph_ids
        )
    )
    _logger.info("Move %s letters to the S10 layout", len(letters))
    letters.write({"template_id": env.ref("sbc_compassion.b2s_l1_s10").id})
