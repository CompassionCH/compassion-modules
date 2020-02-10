##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from . import models
from . import tools
from . import controllers
from . import forms
from . import wizards

from odoo.addons.message_center_compassion.tools.load_mappings import \
    load_mapping_files


def load_mappings(cr, registry):
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
    load_mapping_files(cr, path, files)

