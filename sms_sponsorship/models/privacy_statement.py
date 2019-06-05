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


class PrivacyStatementAgreement(models.Model):
    _inherit = 'privacy.statement.agreement'

    origin_signature = fields.Selection(
        selection_add=[('sms_sponsorship', 'SMS Sponsorship')])
