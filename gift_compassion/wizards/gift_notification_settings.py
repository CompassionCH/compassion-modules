# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class GiftNotificationSettings(models.TransientModel):
    """ Settings configuration for Gift Notifications."""
    _inherit = 'staff.notification.settings'

    # Users to notify
    gift_notify_ids = fields.Many2many(
        'res.partner', 'staff_gift_notification_ids',
        'config_id', 'partner_id',
        string='Gift Undeliverable',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ]
    )

    @api.multi
    def set_gift_notify_ids(self):
        self.env['ir.config_parameter'].set_param(
            'gift_compassion.gift_notify_ids',
            ','.join(map(str, self.gift_notify_ids.ids)))

    @api.model
    def get_default_values(self, _fields):
        res = super(GiftNotificationSettings, self).get_default_values(_fields)
        param_obj = self.env['ir.config_parameter']
        partners = param_obj.get_param(
            'gift_compassion.gift_notify_ids', False)
        if partners:
            res['gift_notify_ids'] = map(int, partners.split(','))
        return res
