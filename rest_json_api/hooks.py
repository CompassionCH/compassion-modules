from odoo.http import Root
from odoo.tools import config

from .http import RestJSONRequest

base_get_request = Root.get_request


def get_request(self, httprequest):
    for endpoint in config.get("rest_json_endpoints", "False").split(","):
        if httprequest.environ["PATH_INFO"].startswith(endpoint):
            return RestJSONRequest(httprequest)
    return base_get_request(self, httprequest)


def post_load():
    """Loaded before any model or data has been initialized.
    This is ok as the post-load hook is for server-wide
    (instead of registry-specific) functionalities.
    This is very useful to create monkey patches for odoo.
    Note: You do not have access to database cursor here.
    """
    Root.get_request = get_request
