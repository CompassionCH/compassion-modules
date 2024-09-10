import base64
import logging

from odoo.tools.misc import file_open

_logger = logging.getLogger(__name__)


def load_mapping_files(env, path, files):
    # This will load json mapping files
    for filename in files:
        _logger.info("loading mapping %s", path + filename)
        with file_open(path + filename) as file_data:
            import_wizard = env["import.json.mapping.wizard"].create(
                {"file": base64.b64encode(file_data.read().encode())}
            )
            import_wizard.import_json_mapping()
