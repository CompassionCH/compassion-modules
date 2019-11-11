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


class StaffNotificationSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""
    _name = 'staff.notification.settings'
    _inherit = 'res.config.settings'

    # Users to notify after Disaster Alert
    disaster_notify_ids = fields.Many2many(
        'res.partner', 'staff_disaster_notification_ids',
        'config_id', 'partner_id',
        string='Disaster Alert',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ]
    )

    @api.multi
    def set_values(self):
        self.env['ir.config_parameter'].set_param(
            'child_compassion.disaster_notify_ids',
            ','.join(map(str, self.disaster_notify_ids.ids)))

    @api.model
    def get_values(self):
        param_obj = self.env['ir.config_parameter']
        res = {}
        partners = param_obj.get_param(
            'child_compassion.disaster_notify_ids', False)
        if partners:
            res['disaster_notify_ids'] = list(map(int, partners.split(',')))
        return res

    @api.model
    def get_param(self, param):
        """ Retrieve a single parameter. """
        return self.sudo().get_values()[param]
