from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.add_fields(
        env,
        [
            (
                "email_from",
                "partner.communication.job",
                "partner_communication_job",
                "char",
                False,
                "partner_communication",
            ),
            (
                "reply_to",
                "partner.communication.job",
                "partner_communication_job",
                "char",
                False,
                "partner_communication",
            ),
        ],
    )
