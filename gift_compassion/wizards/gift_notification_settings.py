# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields


class GiftNotificationSettings(models.TransientModel):
    """ Settings configuration for Gift Notifications."""
    _name = 'gift.notification.settings'
    _inherit = 'res.config.settings'

    # Users to notify
    notify_partner_ids = fields.Many2many(
        'res.partner', string='Notify users',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ]
    )

    @api.multi
    def set_notify_partner_ids(self):
        self.env['ir.config_parameter'].set_param(
            'gift_compassion.notify_users',
            ','.join(map(str, self.notify_partner_ids.ids)))

    @api.model
    def get_default_values(self, _fields):
        param_obj = self.env['ir.config_parameter']
        res = {'notify_partner_ids': False}
        partners = param_obj.get_param(
            'gift_compassion.notify_users', False)
        if partners:
            res['notify_partner_ids'] = map(int, partners.split(','))
        return res

    @api.model
    def get_param(self, param):
        """ Retrieve a single parameter. """
        return self.get_default_values([param])[param]
