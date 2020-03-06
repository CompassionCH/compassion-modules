# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    mobile_notification_id = fields.Many2one(
        'firebase.notification', 'Mobile notification',
        help='Mobile notification sent for a donation confirmation', readonly=False
    )
