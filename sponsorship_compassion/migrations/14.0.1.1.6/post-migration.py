import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # Remove all contracts (Nordic only has Christmas contracts which are no longer used)
    contracts = env["recurring.contract"].search([
        ("type", "=", "O"), ("state", "not in", ["terminated", "cancelled"])])
    contracts.action_contract_terminate()
    contracts.with_context(force_delete=True).unlink()
