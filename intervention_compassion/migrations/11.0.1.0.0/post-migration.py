##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade
from odoo.addons.message_center_compassion.tools import load_mappings


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    path = 'intervention_compassion/static/mappings/'
    files = [
        'commitment_mapping.json',
        'global_intervention_mapping.json',
        'global_intervention_search_mapping.json',
        'hold_create_mapping.json',
        'hold_cancel_mapping.json',
        'hold_create_mapping.json',
        'intervention_mapping.json',
        'intervention_search_mapping.json']

    load_mappings.load_mapping_files(env.cr, path, files)
    # env['import.json.mapping'].python_install_mapping()
