# -*- coding: utf-8 -*-45.00
# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailComposer(models.TransientModel):
    """
    Extend the mail composer so that it can send message to archived partner.
    """
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        res = super(MailComposer, self).send_mail(auto_commit)

        # Re-archive the unarchived recipient.
        unarchived_partners = self.env.context.get('unarchived_partners', [])
        if unarchived_partners:
            self.env['res.partner'].browse(unarchived_partners).toggle_active()

        return res
