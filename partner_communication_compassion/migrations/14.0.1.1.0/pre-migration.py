from openupgradelib import openupgrade


def migrate(cr, version):
    # Move onboarding first B2S letter config to this module.
    openupgrade.rename_xmlids(
        cr,
        [
            (
                "partner_communication_nordic.config_onboarding_first_letter",
                "partner_communication_compassion.config_onboarding_first_letter",
            ),
            (
                "partner_communication_nordic.mail_onboarding_first_letter",
                "partner_communication_compassion.mail_onboarding_first_letter",
            ),
        ],
    )
