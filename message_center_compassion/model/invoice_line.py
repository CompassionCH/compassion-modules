# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields


class account_invoice_line(models.Model):
    """ We add a field for gift instructions. """
    _inherit = "account.invoice.line"

    gift_instructions = fields.Char(compute='_get_instructions')
    need_key = fields.Char(compute='_get_gift_info')

    @api.one
    def _get_gift_info(self):
        need_key = self.contract_id.child_code
        if self.product_id.gmc_name == 'ProjectGift':
            need_key = need_key[:5]
        self.need_key = need_key

    @api.one
    def _get_instructions(self):
        lang = self.partner_id.lang
        product = self.env['product.product'].with_context(
            lang=lang).browse(self.product_id.id)
        if self.product_id.name != self.name and product.name != self.name:
            self.gift_instructions = self.name
