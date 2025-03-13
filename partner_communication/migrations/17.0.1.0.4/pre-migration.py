from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.logged_query(
        cr,
        """
            UPDATE partner_communication_config
            SET send_mode = replace(send_mode, '_only', ''), print_if_not_email = false
            WHERE send_mode LIKE '%_only';
        """,
    )
