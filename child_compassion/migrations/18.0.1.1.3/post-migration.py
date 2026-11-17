from odoo import SUPERUSER_ID, api

from odoo.addons.message_center_compassion.tools.load_mappings import load_mapping_files


def migrate(cr, version):
    """T3697 Reload the household mapping: the member list sent by Connect
    replaces the members of the household, instead of searching members by
    name in all the households (which moved members between households)."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    load_mapping_files(env, "child_compassion/static/mappings/", ["household.json"])
