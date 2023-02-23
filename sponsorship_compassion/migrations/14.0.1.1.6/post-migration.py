import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    christmas = env["product.product"].search([("default_code", "=", "Christmas")])
    sponsors = env["res.partner"].search([("number_sponsorships", ">", 0)])
    _logger.info("Migrating christmas contracts for %s sponsors...", len(sponsors))
    for i, partner in enumerate(sponsors):
        _logger.info("... doing sponsor n° %s/%s", i+1, len(sponsors))
        contracts = partner.other_contract_ids.filtered(lambda c: c.state not in ["cancelled", "terminated"])
        christmas_lines = contracts.mapped("contract_line_ids").filtered(lambda l: l.product_id == christmas)
        if not christmas_lines:
            continue
        partner.with_delay().terminate_christmas_contracts(christmas_lines)
    _logger.info("Migration done!")
