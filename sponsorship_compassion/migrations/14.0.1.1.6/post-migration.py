import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    christmas = env["product.product"].search([("default_code", "=", "Christmas")])
    clines = env["recurring.contract.line"].search(
        [("product_id", "=", christmas.id), ("contract_id.state", "not in", ["terminated", "cancelled"])])
    for partner in clines.mapped("contract_id.partner_id"):
        partner.with_delay().terminate_christmas_contracts(
            partner.other_contract_ids.mapped("contract_line_ids") & clines)
