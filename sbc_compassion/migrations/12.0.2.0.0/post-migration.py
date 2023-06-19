from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    # Update all correspondence texts that are not yet published (the others can be manually corrected as needed)
    correspondence = env["correspondence"].search([(
        "state", "not in", ["Published to Global Partner", "Printed and sent to ICP", "Exception",
                            "Quality check unsuccessful"]
    )])
    correspondence.create_text_boxes()
