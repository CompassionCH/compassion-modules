# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class StaffNotificationSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""
    _name = 'staff.notification.settings'
    _inherit = 'staff.notification.settings'

    # Users to notify after Disaster Alert
    new_partner_notify_ids = fields.Many2many(
        'res.partner', 'staff_sms_notification_ids',
        'config_id', 'partner_id',
        string='SMS new partner',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ]
    )

    @api.multi
    def set_sms_notify_ids(self):
        self.env['ir.config_parameter'].set_param(
            'sms_sponsorship.new_partner_notify_ids',
            ','.join(map(str, self.new_partner_notify_ids.ids)))

    @api.model
    def get_default_values(self, _fields):
        param_obj = self.env['ir.config_parameter']
        res = {}
        partners = param_obj.get_param(
            'sms_sponsorship.new_partner_notify_ids', False)
        if partners:
            res['new_partner_notify_ids'] = map(int, partners.split(','))
        return res

    @api.model
    def get_param(self, param):
        """ Retrieve a single parameter. """
        return self.get_default_values([param])[param]
