from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Repush project status in lifecycle events
    status_mapping = {
        "A": "Active",
        "P": "Phase Out",
        "S": "Suspended",
        "T": "Transitioned",
    }
    for project in env["compassion.project"].search([]):
        project.last_lifecycle_id.project_status = status_mapping[project.status]
        project.status = status_mapping[project.status]
