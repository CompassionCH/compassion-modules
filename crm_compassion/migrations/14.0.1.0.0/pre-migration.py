from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(
        env, [("recurring.contract", "recurring_contract", "user_id", "ambassador_id")]
    )
    openupgrade.add_fields(
        env,
        [
            (
                "user_id",
                "account.move.line",
                "account_move_line",
                "many2one",
                False,
                "crm_compassion",
                False,
            ),
            (
                "event_id",
                "account.move.line",
                "account_move_line",
                "many2one",
                False,
                "crm_compassion",
                False,
            ),
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move_line aml
        SET user_id = il.user_id, event_id = il.event_id
        FROM account_invoice_line il
        WHERE il.id = aml.old_invoice_line_id;
    """,
    )
