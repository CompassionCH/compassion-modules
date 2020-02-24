##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from ..tools.onramp_connector import TestOnrampConnector

from odoo import api, models, fields


class GetLetterImageWizard(models.Model):
    """ Send any message to any ONRAMP.
    """
    _name = 'onramp.simulator'
    _description = 'Get Letter & Image Wizard'

    name = fields.Char()
    action_id = fields.Many2one('gmc.action.connect', 'Message Type', readonly=False)
    server_url = fields.Char(default='http://localhost:8069/onramp')
    message_type_url = fields.Char(
        related='action_id.connect_schema')
    body_json = fields.Text()
    result = fields.Text()
    result_code = fields.Text()

    @api.multi
    def send_message(self):
        connector = TestOnrampConnector()
        connector.test_message(self)
