# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models, api
from odoo.tools.safe_eval import safe_eval


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'


    @api.multi
    def get_needaction_data(self):
        """ add manually the counter for only one menu an not for all
        menus of a model, doesn't use _needaction_count method """
        res = super(IrUiMenu, self).get_needaction_data()

        # add manually the counter for only
        # one menu an not for all menus of a model
        menu_follow_sds = \
            self.env.ref('sponsorship_tracking.menu_follow_sds')
        domain = safe_eval(menu_follow_sds.action.domain)
        model = menu_follow_sds.action.res_model
        counter = \
            len(self.env[model].search(domain, limit=100, order='id DESC'))

        res[menu_follow_sds.id]['needaction_enabled'] = True
        res[menu_follow_sds.id]['needaction_counter'] = counter

        return res
