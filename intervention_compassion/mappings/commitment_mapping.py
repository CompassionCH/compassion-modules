##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.addons.message_center_compassion.mappings.base_mapping \
    import OnrampMapping


class CommitmentCreateMapping(OnrampMapping):
    """ Commitment Creation Mapping
    """

    ODOO_MODEL = 'compassion.intervention.commitment.wizard'

    CONNECT_MAPPING = {
        "Intervention_ID": ("intervention_id.intervention_id",
                            "compassion.intervention"),
        "Commitment_Amount": "commitment_amount",
        "HoldID": "hold_id",
        "IsRequestedAdditionalFundCommitted": "commit_to_additional_fund",
    }

    FIELDS_TO_SUBMIT = {
        "GlobalPartner_ID": None,
        "Intervention_ID": None,
        "Commitment_Amount": None,
        "HoldID": None,
        "IsRequestedAdditionalFundCommitted": None,
    }

    CONSTANTS = {
        "GlobalPartner_ID": 'CH'
    }
