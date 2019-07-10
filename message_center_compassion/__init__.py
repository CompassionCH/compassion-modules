from odoo import api, SUPERUSER_ID
from . import models
from . import tools
from . import controllers
from . import wizards


def load_mappings(cr, registry):
    path = 'message_center_compassion/static/mappings/'
    files = ['advanced_query_mapping.json']
    tools.load_mappings.load_mapping_files(cr, path, files)
