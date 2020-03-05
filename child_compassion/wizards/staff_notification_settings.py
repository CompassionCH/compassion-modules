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
    _inherit = 'res.config.settings'

    # Users to notify after Disaster Alert
    disaster_notify_ids = fields.Many2many(
        'res.partner',
        string='Disaster Alert',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ],
        compute='_compute_relation_disaster_notify_ids',
        inverse='_inverse_relation_disaster_notify_ids'
    )

    def _compute_relation_disaster_notify_ids(self):
        self.disaster_notify_ids = self._get_disaster_notify_ids()

    @api.model
    def _get_disaster_notify_ids(self):
        param_obj = self.env['ir.config_parameter'].sudo()
        partners = param_obj.get_param(
            'child_compassion.disaster_notify_ids', False)
        if partners:
            return [
                (6, 0, list(map(int, partners.split(','))))
            ]
        else:
            return False

    def _inverse_relation_disaster_notify_ids(self):
        self.env['ir.config_parameter'].set_param(
            'child_compassion.disaster_notify_ids',
            ','.join(map(str, self.disaster_notify_ids.ids)))

    @api.model
    def get_values(self):
        res = super().get_values()
        res['disaster_notify_ids'] = self._get_disaster_notify_ids()
        return res
