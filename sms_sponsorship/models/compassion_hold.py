##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class AbstractHold(models.AbstractModel):
    _inherit = 'compassion.abstract.hold'

    channel = fields.Selection(selection_add=[
        ('sms', 'SMS sponsorship service')
    ])


class CompassionHold(models.Model):
    _inherit = 'compassion.hold'

    sms_request_id = fields.Many2one('sms.child.request')

    @api.multi
    def hold_released(self, vals=None):
        self.sms_request_id.write({
            'state': 'expired'
        })
        return super().hold_released(vals)
