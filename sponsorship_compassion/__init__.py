##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from . import models
from . import wizards
from odoo.addons.message_center_compassion.tools.load_mappings \
    import load_mapping_files


def load_mappings(cr, registry):
    path = "sponsorship_compassion/static/mappings/"
    files = [
        "anonymize_partner.json",
        "cancel_sponsorship.json",
        "create_sponsorship.json",
        "upsert_partner.json",
    ]
    load_mapping_files(cr, path, files)
