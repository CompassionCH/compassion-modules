# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from odoo.addons.message_center_compassion.mappings.base_mapping \
    import OnrampMapping


class HoldCreateMapping(OnrampMapping):
    """ Hold Creation Mapping
    """
    ODOO_MODEL = 'compassion.intervention.hold.wizard'

    CONNECT_MAPPING = {
        "Intervention_ID": "intervention_id.intervention_id",
        "ExpirationDate": "expiration_date",
        "HoldAmount": "hold_amount",
        "HoldID": "hold_id",
        "NextYearOptIn": "next_year_opt_in",
        "PrimaryOwner": ("primary_owner.name", "res.users"),
        "SecondaryOwner": "secondary_owner",
        "ServiceLevelAgreement": "service_level",
    }

    FIELDS_TO_SUBMIT = {
        "GlobalPartner_ID": None,
        "Intervention_ID": None,
        "ExpirationDate": None,
        "HoldAmount": None,
        "PrimaryOwner": None,
        "SecondaryOwner": None,
        "ServiceLevelAgreement": None,
        "NextYearOptIn": None,
    }

    CONSTANTS = {
        "GlobalPartner_ID": 'CH'
    }


class HoldUpdateMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.intervention'

    MAPPING_NAME = 'update_hold'

    def __init__(self, env):
        super(HoldUpdateMapping, self).__init__(env)
        self.CONNECT_MAPPING = HoldCreateMapping.CONNECT_MAPPING
        self.FIELDS_TO_SUBMIT = HoldCreateMapping.FIELDS_TO_SUBMIT
        self.CONSTANTS = HoldCreateMapping.CONSTANTS
        self.CONNECT_MAPPING['Intervention_ID'] = 'intervention_id'
        self.FIELDS_TO_SUBMIT['HoldID'] = None


class HoldCancelMapping(OnrampMapping):
    """ Hold Cancellation Mapping
    """

    ODOO_MODEL = 'compassion.intervention'
    MAPPING_NAME = 'cancel_hold'

    CONNECT_MAPPING = {
        "Intervention_ID": "intervention_id",
        "Intervention_HoldID": "hold_id",
    }

    FIELDS_TO_SUBMIT = {
        "GlobalPartner_ID": None,
        "Intervention_ID": None,
        "Intervention_HoldID": None,
    }

    CONSTANTS = {
        "GlobalPartner_ID": 'CH'
    }
