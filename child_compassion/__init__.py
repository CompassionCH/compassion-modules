from odoo.addons.message_center_compassion.tools.load_mappings import load_mapping_files

from . import controllers, models, wizards


def load_mappings(cr, registry):
    path = "child_compassion/static/mappings/"
    files = [
        "household_member.json",
        "household.json",
        "child.json",
        "child_cdpr.json",
        "child_lifecycle.json",
        "child_note.json",
        "childpool_advanced_search.json",
        "childpool_rich_mix.json",
        "childpool_simple_search.json",
        "childpool_search_response.json",
        "childpool_search_fields.json",
        "demand_planning.json",
        "disaster_alert.json",
        "fcp.json",
        "fcp_lifecycle.json",
        "field_office.json",
        "global_child.json",
        "hold_create.json",
        "hold_release.json",
        "reservation_cancel.json",
        "reservation_child.json",
        "reservation_project.json",
    ]
    load_mapping_files(cr, path, files)
