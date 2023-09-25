from . import controllers, models, tools, wizards


def load_mappings(cr, registry):
    path = "message_center_compassion/static/mappings/"
    files = ["advanced_query_mapping.json"]
    tools.load_mappings.load_mapping_files(cr, path, files)
