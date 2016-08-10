# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models


class portal_wizard(models.TransientModel):
    """ This class creates analytic accounts for new portal users."""

    _inherit = 'portal.wizard'

    @api.multi
    def action_apply(self):
        self.ensure_one()
        res = super(portal_wizard, self).action_apply()
        for user in self.user_ids:
            users = self.env['res.users'].with_context(
                lang='en_US').search([('name', '=', user.partner_id.name)])
            partner_name = user.partner_id.name

            if user.partner_id and user.partner_id.parent_id:
                partner_name = user.partner_id.parent_id.name + \
                    ", " + partner_name

            analytics_obj = self.env['account.analytic.account'].with_context(
                lang='en_US')
            acc_ids = analytics_obj.search([('name', '=', partner_name)])
            if not acc_ids and users:
                acode = self.env['ir.sequence'].get(
                    'account.analytic.account')
                parent_id = analytics_obj.search(
                    [('name', '=', 'Partners')]).ids[0]
                analytics_obj.create({
                    'name': partner_name,
                    'type': 'normal',
                    'code': acode,
                    'parent_id': parent_id,
                    'manager_id': users.ids[0],
                    'use_timesheets': True,
                })

        return res
