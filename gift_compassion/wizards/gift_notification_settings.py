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
    _inherit = 'res.config.settings'

    # Users to notify
    gift_notify_ids = fields.Many2many(
        'res.partner',
        string='Gift Undeliverable',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ],
        compute='_compute_relation_gift_notify_ids',
        inverse='_inverse_relation_gift_notify_ids', readonly=False
    )

    def _compute_relation_gift_notify_ids(self):
        self.gift_notify_ids = self._get_gift_notify_ids()

    @api.model
    def _get_gift_notify_ids(self):
        param_obj = self.env['ir.config_parameter']
        partners = param_obj.get_param(
            'gift_compassion.gift_notify_ids', False)
        if partners:
            return [
                (6, 0, list(map(int, partners.split(','))))
            ]
        else:
            return False

    def _inverse_relation_gift_notify_ids(self):
        self.env['ir.config_parameter'].set_param(
            'gift_compassion.gift_notify_ids',
            ','.join(map(str, self.gift_notify_ids.ids)))

    @api.model
    def get_values(self):
        res = super().get_values()
        res['gift_notify_ids'] = self._get_gift_notify_ids()
        return res
