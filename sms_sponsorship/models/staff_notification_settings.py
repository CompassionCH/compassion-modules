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
    sms_new_partner_notify_ids = fields.Many2many(
        'res.partner',
        string='SMS new partner',
        domain=[('user_ids', '!=', False)],
        compute='_compute_relation_sms_new_partner_notify_ids',
        inverse='_inverse_relation_sms_new_partner_notify_ids', readonly=False)

    def _inverse_relation_sms_new_partner_notify_ids(self):
        self.env['ir.config_parameter'].set_param(
            'sms_sponsorship.sms_new_partner_notify_ids',
            ','.join(map(str, self.sms_new_partner_notify_ids.ids)))

    def _compute_relation_sms_new_partner_notify_ids(self):
        self.sms_new_partner_notify_ids = self._get_sms_new_partner_notify_ids()

    @api.model
    def _get_sms_new_partner_notify_ids(self):
        param_obj = self.env['ir.config_parameter']
        partners = param_obj.get_param(
            'sms_sponsorship.sms_new_partner_notify_ids', False)
        if partners:
            return [(6, 0, list(map(int, partners.split(','))))]
        else:
            return False

    @api.model
    def get_values(self):
        res = super().get_values()
        res['sms_new_partner_notify_ids'] = self._get_sms_new_partner_notify_ids()
        return res
