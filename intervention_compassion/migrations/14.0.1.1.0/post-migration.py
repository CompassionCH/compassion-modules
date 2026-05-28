from odoo.addons.message_center_compassion.tools.load_mappings import load_mapping_files


def migrate(cr, version):
    # Load new mappings
    path = "intervention_compassion/static/mappings/"
    files = [
        "global_intervention_mapping.json",
        "hold_create_mapping.json",
        "hold_update_mapping.json",
        "intervention_fcp_reservation.json",
        "intervention_mapping.json",
        "reservation_cancel_mapping.json",
        "reservation_create_mapping.json",
        "reservation_update_mapping.json",
    ]
    load_mapping_files(cr, path, files)
