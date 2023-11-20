##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.tools.load_mappings import load_mapping_files

from . import controllers, models, tools, wizards


def load_mappings(cr, registry):
    path = "sbc_compassion/static/mappings/"
    files = [
        "page_mapping.json",
        "correspondence_mapping.json",
    ]
    load_mapping_files(cr, path, files)
