import logging

from openupgradelib.openupgrade import migrate

from odoo.tools import email_normalize_all, flatten

_logger = logging.getLogger(__name__)


@migrate()
def migrate(env, version):
    cr = env.cr
    cr.execute(
        """
        DELETE FROM ir_model_fields_selection
        WHERE field_id = (
            SELECT id FROM ir_model_fields WHERE name = 'origin_signature')
    """
    )

    # Migrate privacy_statements that were used for "opt-in".
    cr.execute(
        """
        SELECT partner_id FROM privacy_statement_agreement
        WHERE agreement_date <= '2022-11-08'
    """
    )
    partner_ids = [r[0] for r in cr.fetchall()]
    opt_out_partners = env["res.partner"].search(
        [("email", "like", "@"), ("id", "not in", partner_ids)]
    )
    env["mail.blacklist"].create(
        [
            {
                "email": email,
            }
            for email in flatten(map(email_normalize_all, opt_out_partners.mapped(
                "email")))
        ]
    )
