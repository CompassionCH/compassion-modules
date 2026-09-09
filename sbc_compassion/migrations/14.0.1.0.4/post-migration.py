import datetime

from openupgradelib import openupgrade

# A letter only ever reaches "Exception" for a benign hold via create_commkit()/
# hold_letters(), both of which post a chatter message with one of these exact
# subjects in the same call that sets the state - durable, per-letter evidence
# of *why* this specific letter is held, as opposed to just checking whether
# the project/template is currently in a hold-worthy state (which a letter
# stuck in "Exception" for a genuine failure, e.g. a compose failure, could
# coincidentally also match).
HOLD_MESSAGE_SUBJECTS = ["Project suspended", "Christmas Hold"]


@openupgrade.migrate()
def migrate(env, version):
    if version:
        # Backfill on_hold=True on letters already stuck in "Exception" only
        # because they were deliberately queued (project suspended, or a
        # Christmas letter outside the Christmas period), so they immediately
        # reappear on MyCompassion instead of only on the next
        # hold/reactivate cycle. Restricted to letters whose project/template
        # is *currently* in that state too, to keep this backfill narrowly
        # scoped to the case this ticket reported - a letter with hold
        # evidence whose project has since been reactivated is a separate,
        # pre-existing concern (why didn't reactivate_letters() clear it?),
        # not something to fix here.
        letters = env["correspondence"].search(
            [
                ("state", "=", "Exception"),
                ("direction", "=", "Supporter To Beneficiary"),
                ("kit_identifier", "=", False),
                ("child_id.project_id.hold_s2b_letters", "=", True),
                ("message_ids.subject", "in", HOLD_MESSAGE_SUBJECTS),
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
                    ("message_ids.subject", "in", HOLD_MESSAGE_SUBJECTS),
                ]
            )

        letters.write({"on_hold": True})
        # is_published (my_compassion, if installed) is backfilled in that
        # module's own migration instead of here: my_compassion loads after
        # sbc_compassion in the dependency graph, so its fields are not yet
        # registered on this model at this point.
