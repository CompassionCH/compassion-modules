##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade
from sponsorship_compassion.tools import load_mappings


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    path = 'sponsorship_compassion/static/mappings/'
    files = ['anonymize_partner_mapping.json',
             'sponsorship_base_mapping.json',
             'upsert_mapping.json']

    load_mappings.load_mapping_files(env.cr, path, files)
