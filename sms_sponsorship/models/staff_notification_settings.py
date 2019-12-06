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
    _inherit = 'res.config.settings'

    # Users to notify when new partner make a sponsorship by SMS
    new_partner_notify_ids = fields.Many2many(
        'res.partner', relation="staff_sms_notification_settings",
        string='SMS new partner')

    @api.multi
    def set_new_partner_notify_ids(self):
        self.env['ir.config_parameter'].set_param(
            'sms_sponsorship.new_partner_notify_ids',
            ','.join(map(str, self.new_partner_notify_ids.ids)))

    @api.model
    def get_default_values(self, _fields):

        param_obj = self.env['ir.config_parameter']
        res = super().get_default_values(_fields)
        res['new_partner_notify_ids'] = False
        partners = param_obj.get_param(
            'sms_sponsorship.new_partner_notify_ids', False)
        if partners:
            res['new_partner_notify_ids'] = list(map(int, partners.split(',')))
        return res
