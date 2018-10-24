# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Philippe Heer <heerphilippe@msn.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class ReinstatementMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.hold'
    MAPPING_NAME = 'new_reinstatement_notification'

    CONNECT_MAPPING = {
        'BeneficiaryState': 'type',
        'HoldID': 'hold_id',
        'PrimaryHoldOwner': ('primary_owner.name', 'res.users'),
        'BeneficiaryReinstatementReason': 'reinstatement_reason',
        'Beneficiary_GlobalID': ('child_id.global_id', 'compassion.child'),

        # Not used in Odoo
        'GlobalPartner_ID': None,
        'FCP_ID': None,
    }

    CONSTANTS = {

    }
