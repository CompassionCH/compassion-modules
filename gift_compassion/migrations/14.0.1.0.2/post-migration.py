from openupgradelib import openupgrade

from odoo.addons.recurring_contract.tools import chunks


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    moves = env["account.move"].search(
        [("ref", "=", "Gift payment to GMC"), ("payment_state", "!=", "paid")]
    )
    for mv_subset in chunks(moves, 80):
        mv_subset.button_draft()
        mv_subset.button_cancel()
        gifts = env["sponsorship.gift"].search([("payment_id", "in", mv_subset.ids)])
        inverse_moves = gifts.mapped("inverse_payment_id")
        if inverse_moves:
            inverse_moves.button_draft()
            inverse_moves.button_cancel()
        gifts.write({"payment_id": False, "inverse_payment_id": False})
