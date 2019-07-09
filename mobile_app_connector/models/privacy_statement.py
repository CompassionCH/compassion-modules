# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class PrivacyStatementAgreement(models.Model):
    _inherit = 'privacy.statement.agreement'

    origin_signature = fields.Selection(
        selection_add=[('mobile_app', 'Mobile App Registration')])

    def mobile_get_privacy_notice(self, language):
        return {'PrivacyNotice': self.env['compassion.privacy.statement']
                .with_context(lang=language)
                .sudo().search([], limit=1).text}
