##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Benoît Schopfer <mails@benoitschopfer.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade

from odoo.addons.message_center_compassion.tools.load_mappings import \
    load_mapping_files


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # path = 'gift_compassion/static/mappings/'
    # files = [
    #     'mapping.json',
    # ]
    # load_mapping_files(env.cr, path, files)

    env['import.json.mapping'].python_install_mapping()
