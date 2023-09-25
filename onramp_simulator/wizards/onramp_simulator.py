##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models

from ..tools.onramp_connector import TestOnrampConnector


class GetLetterImageWizard(models.Model):
    """Send any message to any ONRAMP."""

    _name = "onramp.simulator"
    _description = "Get Letter & Image Wizard"

    name = fields.Char()
    action_id = fields.Many2one("gmc.action.connect", "Message Type", readonly=False)
    server_url = fields.Char(
        default=lambda s: s.env["ir.config_parameter"].sudo().get_param("web.base.url")
    )
    message_type_url = fields.Char(related="action_id.connect_schema")
    body_json = fields.Text()
    result = fields.Text()
    result_code = fields.Text()

    def send_message(self):
        connector = TestOnrampConnector(self.env)
        connector.test_message(self)
