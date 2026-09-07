import datetime

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if version:
        # Backfill on_hold=True on letters already stuck in "Exception" only
        # because they were deliberately queued (project suspended, or a
        # Christmas letter outside the Christmas period), so they immediately
        # reappear on MyCompassion instead of only on the next
        # hold/reactivate cycle.
        letters = env["correspondence"].search(
            [
                ("state", "=", "Exception"),
                ("direction", "=", "Supporter To Beneficiary"),
                ("kit_identifier", "=", False),
                ("child_id.project_id.hold_s2b_letters", "=", True),
            ]
        )

        in_christmas_period = env["res.config.settings"].is_in_christmas_period(
            datetime.date.today()
        )
        if not in_christmas_period:
            letters |= env["correspondence"].search(
                [
                    ("state", "=", "Exception"),
                    ("direction", "=", "Supporter To Beneficiary"),
                    ("kit_identifier", "=", False),
                    ("template_id.is_christmas_letter", "=", True),
                ]
            )

        letters.write({"on_hold": True})
        # is_published (my_compassion, if installed) is backfilled in that
        # module's own migration instead of here: my_compassion loads after
        # sbc_compassion in the dependency graph, so its fields are not yet
        # registered on this model at this point.
