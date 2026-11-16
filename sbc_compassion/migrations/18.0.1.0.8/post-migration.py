import json
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # T3646: S10 letters printing their translation over page 2's printed text
    kit_identifiers = set()
    for message in env["gmc.message"].search([("content", "like", "-1S10-")]):
        try:
            content = json.loads(message.content)
        except (TypeError, ValueError):
            continue
        if not isinstance(content, dict):
            continue
        # A message can hold several letters, each with its own template
        for response in content.get("Responses") or [content]:
            if isinstance(response, dict) and "-1S10-" in (
                response.get("Template") or ""
            ):
                kit_identifiers.add(response.get("CompassionSBCId"))
    letters = env["correspondence"].search(
        [
            ("kit_identifier", "in", list(kit_identifiers - {None})),
            ("template_id", "=", env.ref("sbc_compassion.b2s_l1").id),
        ]
    )
    letters = letters.filtered(
        lambda letter: any(
            len((paragraph.translated_text or "").strip()) >= 5
            for paragraph in letter.page_ids[1:2].paragraph_ids
        )
    )
    _logger.info("Move %s letters to the S10 layout", len(letters))
    letters.write({"template_id": env.ref("sbc_compassion.b2s_l1_s10").id})
