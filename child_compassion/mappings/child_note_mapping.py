# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class ChildNoteMapping(OnrampMapping):
    """
    Child Note Mapping
    """
    ODOO_MODEL = 'compassion.child.note'
    MAPPING_NAME = 'beneficiary_note'

    CONNECT_MAPPING = {
        'GlobalID': ('child_id.global_id', 'compassion.child'),
        'Body': 'body',
        'RecordType': 'record_type',
        'Type': 'type',
        'Visibility': 'visibility',
        'SourceKitName': 'source_code',
    }
