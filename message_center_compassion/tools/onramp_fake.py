##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
"""Set ``connect_fake = True`` in the Odoo configuration file to answer the
outgoing messages here instead of sending them, so that the flows going through
GMC can be run on a development database without reaching the real Compassion
Connect.
"""

import logging
from uuid import uuid4

from odoo.tools.config import config
from odoo.tools.misc import str2bool

_logger = logging.getLogger(__name__)

FAKE_ENDPOINTS = {
    "beneficiaries/holds": (
        "BeneficiaryHoldRequestList",
        "BeneficiaryHoldResponseList",
        "HoldID",
    ),
    "supporters": ("SupporterProfile", "SupporterProfileResponse", "GlobalID"),
    "supporters/sponsorships": (
        "BeneficiaryCommitmentList",
        "BeneficiaryCommitmentResponseList",
        "Commitment_ID",
    ),
}


def is_enabled():
    """Whether the connector answers itself instead of calling Connect."""
    return str2bool(config.get("connect_fake") or False, False)


def fake_send_message(service_name, message_type, body=None, **kwargs):
    endpoint = service_name.removeprefix("/")
    if message_type == "GET_RAW":
        _logger.warning("No fake content for the %s GMC file", endpoint)
        return b""
    answer = FAKE_ENDPOINTS.get(endpoint)
    if answer is None:
        _logger.warning("No fake answer for the %s GMC endpoint", endpoint)
        return {
            "code": 404,
            "request_id": uuid4().hex,
            "Error": f"No fake answer for the {endpoint} GMC endpoint",
        }
    outgoing_wrapper, answer_wrapper, id_field = answer
    sent = (body or {}).get(outgoing_wrapper, body or {})
    if not isinstance(sent, list):
        sent = [sent]
    _logger.info("Faking the answer of GMC to %s %s", message_type, endpoint)
    return {
        "code": 200,
        "request_id": uuid4().hex,
        "content": {
            answer_wrapper: [
                {
                    "Code": 2000,
                    "Message": "Success",
                    id_field: obj.get(id_field) or uuid4().hex,
                }
                for obj in sent
            ]
        },
    }


if is_enabled():
    _logger.warning(
        "connect_fake is set: the messages to GMC are answered locally and "
        "nothing reaches Compassion Connect."
    )
