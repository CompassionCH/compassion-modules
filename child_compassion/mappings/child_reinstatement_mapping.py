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
import logging
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping

_logger = logging.getLogger(__name__)


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
        'ICP_ID': None,
    }

    CONSTANTS = {

    }

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """
        Don't update Hold Owner and avoid security restrictions if
        owner is in another company.
        """
        if connect_name == 'PrimaryHoldOwner':
            return {}
        return super(ReinstatementMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search)

    def get_connect_data(self, odoo_object, fields_to_submit=None):
        """
        Prevents security restrictions to get the Primary Owner name
        in case the user that made the hold is in another Company.
        """
        if fields_to_submit is None:
            fields_to_submit = self.FIELDS_TO_SUBMIT.keys()
        try:
            fields_to_submit.remove('PrimaryHoldOwner')
        except ValueError:
            _logger.warning('No primary owner for reinstatement mapping')
        res = super(ReinstatementMapping, self).get_connect_data(
            odoo_object, fields_to_submit)
        res['PrimaryHoldOwner'] = odoo_object.sudo().primary_owner.name
        return res
