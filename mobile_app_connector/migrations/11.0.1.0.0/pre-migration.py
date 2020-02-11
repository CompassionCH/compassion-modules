##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade
from message_center_compassion.tools import load_mappings


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    path = 'mobile_app_connector/static/mappings/'
    files = [
        'app_banner_mapping.json',
        'compassion_child_mapping.json',
        'compassion_donation_mapping.json',
        'compassion_login_mapping.json',
        'compassion_mobile_correspondence_mapping.json',
        'compassion_project_mapping.json',
        'from_letter_mapping.json',
        'mobile_app_tile_mapping.json',
        'mobile_child_picture_mapping.json',
        'wp_post_mapping.json',
    ]
    load_mappings.load_mapping_files(env.cr, path, files)
