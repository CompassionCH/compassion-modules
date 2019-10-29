##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from . import models
from . import wizards
from odoo.addons.message_center_compassion.tools.load_mappings import \
    load_mapping_files


def load_mappings(cr, registry):
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

    load_mapping_files(cr, path, files)
