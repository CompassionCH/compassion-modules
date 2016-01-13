# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import ast
from openerp import api, models


class IrUiMenu(models.Model):

    _inherit = 'ir.ui.menu'

    @api.multi
    def get_needaction_data(self):
        res = dict()
        for menu in self:
            new_context = dict()
            if (menu.action and hasattr(menu.action, 'context') and
                    menu.action.context):
                try:
                    new_context = ast.literal_eval(menu.action.context)
                    new_context.update(self.env.context)
                except:
                    new_context = self.env.context
            res.update(
                super(IrUiMenu,
                      menu.with_context(new_context)).get_needaction_data())
        return res
