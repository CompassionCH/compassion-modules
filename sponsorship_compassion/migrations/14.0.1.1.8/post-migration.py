import logging
from openupgradelib import openupgrade
from odoo.addons.message_center_compassion.tools.onramp_connector import OnrampConnector

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    _logger.info("Start migrating commitment")
    onramp = OnrampConnector(env)
    # Search for all contraact with a commitment
    contracts = env["recurring.contract"].search([
        ("type", "ilike", "S"), ("state", "=", "active"), ("gmc_correspondent_commitment_id", "=", False)])
    for contract in contracts:
        global_id = contract.child_id.global_id
        _logger.info(f"Migrating {global_id} child on {contract.gmc_commitment_id} contract")
        answer = onramp.send_message(f"beneficiaries/{global_id}/summary", "GET")
        commitments = answer.get("content").get("Commitments") if answer.get("code") == 200 else False
        if commitments:
            for commitment in commitments:
                if commitment.get("EndDate"):
                    _logger.info(f"Commitment skipped it has an enddate {commitment}")
                    continue
                if commitment.get("CommitmentType") == "Sponsor":
                    new_gmc_id = commitment.get('CommitmentID')
                    if new_gmc_id:
                        _logger.info(f"Commitment used to assign gmc_commitment_id \n"
                                     f"current :{contract.gmc_commitment_id}\n"
                                     f"new :{new_gmc_id}")
                        contract.gmc_commitment_id = new_gmc_id
                    partner = env['res.partner'].search_read([
                        ('global_id', '=', commitment.get("SupporterID"))], ['id'])
                    contract.gmc_payer_partner_id = partner[0].get("id") if partner else False
                elif commitment.get("CommitmentType") == "Correspondent":
                    _logger.info(f"Commitment used to assign gmc_commitment_id \n"
                                 f"current :{contract.gmc_correspondent_commitment_id}\n"
                                 f"new :{commitment.get('CommitmentID')}")
                    contract.gmc_correspondent_commitment_id = commitment.get("CommitmentID")
    _logger.info("End of commitment migration")
