# -*- coding: utf-8 -*-45.00
# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailComposer(models.TransientModel):
    """
    Extend the mail composer so that it can send message to archived partner,
    and put back the selected partner in the claim in case it was not linked.
    """
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):

        unarchived_ids = self.env.context.get('unarchived_partners', [])
        if unarchived_ids:
            unarchived_res = self.env['res.partner'].browse(unarchived_ids)
            unarchived_res.toggle_active()

        res = super(MailComposer, self).send_mail(auto_commit)

        # Re-archive the unarchived recipient.
        if unarchived_ids:
            unarchived_res.toggle_active()

        # Put back selected partner into claim
        if self.env.context.get('claim_no_partner'):
            gen_mail = self.env['mail.mail'].search([
                ('res_id', '=', self.res_id),
                ('model', '=', 'crm.claim')
            ], limit=1)
            self.env['crm.claim'].browse(self.res_id).write({
                'partner_id': gen_mail.recipient_ids[:1].id
            })

        return res
