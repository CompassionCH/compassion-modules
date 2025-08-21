from . import onramp_fastapi
from . import models
from . import tools
from . import wizards


def load_mappings(env):
    path = "message_center_compassion/static/mappings/"
    files = ["advanced_query_mapping.json"]
    tools.load_mappings.load_mapping_files(env, path, files)
