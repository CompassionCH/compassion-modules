import base64
from odoo import api, SUPERUSER_ID
from odoo.tools.misc import file_open


def load_mapping_files(cr, path, files):
    # This will load json mapping files
    env = api.Environment(cr, SUPERUSER_ID, {})
    for filename in files:
        with file_open(path + filename) as file_data:
            import_wizard = env['import.json.mapping.wizard'].create({
                'file': base64.b64encode(file_data.read().encode())
            })
            import_wizard.import_json_mapping()
