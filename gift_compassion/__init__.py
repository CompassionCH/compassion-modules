##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.tools.load_mappings import \
    load_mapping_files

from . import models
from . import wizards


def load_mappings(cr, registry):
    path = 'gift_compassion/static/mappings/'
    files = [
        'mapping.json',
    ]
    load_mapping_files(cr, path, files)
