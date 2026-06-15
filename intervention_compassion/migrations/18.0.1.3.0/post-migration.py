from odoo import SUPERUSER_ID, api

from odoo.addons.message_center_compassion.tools.load_mappings import load_mapping_files


def migrate(cr, version):
    # Load new mappings
    path = "intervention_compassion/static/mappings/"
    files = [
        "global_intervention_mapping.json",
        "global_intervention_search_mapping.json",
        "hold_create_mapping.json",
        "hold_update_mapping.json",
        "intervention_fcp_reservation.json",
        "intervention_mapping.json",
        "reservation_cancel_mapping.json",
        "reservation_create_mapping.json",
        "reservation_update_mapping.json",
    ]
    env = api.Environment(cr, SUPERUSER_ID, {})
    load_mapping_files(env, path, files)
    load_mapping_files(env, "child_compassion/static/mappings/", ["fcp.json"])
