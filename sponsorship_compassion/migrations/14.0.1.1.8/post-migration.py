from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Search for all contracts with a commitment
    contracts = env["recurring.contract"].search(
        [
            ("type", "ilike", "S"),
            ("state", "=", "active"),
            ("gmc_correspondent_commitment_id", "=", False),
        ]
    )
    for contract in contracts:
        # Postpone migration one hour after, with low priority
        contract.with_delay(
            eta=3600, priority=50
        ).migrate_gmc_correspondence_commitment()
