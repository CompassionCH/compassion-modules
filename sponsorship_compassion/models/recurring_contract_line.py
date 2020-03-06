##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models
from lxml import etree

from .product_names import SPONSORSHIP_CATEGORY, FUND_CATEGORY


class SponsorshipLine(models.Model):
    _inherit = 'recurring.contract.line'

    contract_type = fields.Selection([
        ('G', 'Child Gift'),
        ('S', 'Sponsorship'),
        ('SC', 'Correspondence')
    ], related='contract_id.type', readonly=True)
    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship', ondelete='cascade', readonly=False
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        """ Hide field sponsorship_id for sponsorships.
        """
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        if view_type == 'tree':
            s_type = self._context.get('default_type', 'O')
            if 'S' in s_type:
                # Remove field sponsorship_id for sponsorship contracts
                doc = etree.XML(res['arch'])
                for node in doc.xpath("//field[@name='sponsorship_id']"):
                    node.getparent().remove(node)
                res['arch'] = etree.tostring(doc)
                del (res['fields']['sponsorship_id'])

        return res

    @api.onchange('contract_type')
    def onchange_type(self):
        """ Change domain of product depending on type of contract. """
        res = dict()
        if 'S' in self.contract_id.type:
            res['domain'] = {
                'product_id': [('categ_name', 'in', [SPONSORSHIP_CATEGORY,
                                                     FUND_CATEGORY])]
            }
        else:
            res['domain'] = {
                'product_id': [('categ_name', '!=', SPONSORSHIP_CATEGORY)]
            }
        return res
