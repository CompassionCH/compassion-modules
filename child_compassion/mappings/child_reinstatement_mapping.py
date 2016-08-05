# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Philippe Heer <heerphilippe@msn.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class ReinstatementMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.hold'
    MAPPING_NAME = 'new_reinstatement_notification'

    CONNECT_MAPPING = {
        'BeneficiaryState': 'type',
        'BeneficiaryOrder_ID': 'hold_id',
        'PrimaryHoldOwner': 'primary_owner',
        'BeneficiaryReinstatementReason': 'reinstatement_reason',
        'Beneficiary_GlobalID': ('child_id.global_id', 'compassion.child'),

        # Not used in Odoo
        'GlobalPartner_ID': None,
        'ICP_ID': None,
    }

    CONSTANTS = {

    }

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        if connect_name == 'Beneficiary_GlobalID':
            relation_search = [('active', '=', False)]
        return super(ReinstatementMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search)
