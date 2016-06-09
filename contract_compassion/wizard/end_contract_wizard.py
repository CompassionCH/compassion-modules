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

from openerp import models, fields, api
from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from lxml import etree
from datetime import datetime


class EndContractWizard(models.TransientModel):
    _name = 'end.contract.wizard'

    end_date = fields.Date(
        required=True, default=datetime.today().strftime(DF))
    contract_id = fields.Many2one(
        'recurring.contract', 'Contract',
        default=lambda self: self.env.context.get('active_id'))
    child_id = fields.Many2one(
        'compassion.child', 'Child',
        default=lambda self: self._get_child_id())
    end_reason = fields.Selection('_get_end_reason', required=True)
    do_transfer = fields.Boolean('I want to transfer the child')
    transfer_country_id = fields.Many2one(
        'compassion.global.partner', 'Country')

    @api.model
    def _get_child_id(self):
        # Retrieve the id of the sponsored child
        contract = self.env['recurring.contract'].browse(
            self.env.context.get('active_id'))
        return contract.child_id.id if contract.child_id else False

    def _get_end_reason(self):
        return self.env['recurring.contract'].get_ending_reasons()

    @api.v7
    def fields_view_get(self, cr, user, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(EndContractWizard, self).fields_view_get(
            cr, user, view_id, view_type, context, toolbar, submenu)
        # If there is no child in contract, hide field
        if view_type == 'form' and not self._get_child_id(cr, user, context):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='child_id']"):
                node.set('invisible', "1")
                orm.setup_modifiers(node, res['fields']['child_id'])
            res['arch'] = etree.tostring(doc)

        return res

    @api.multi
    def end_contract(self):
        self.ensure_one()
        contract = self.contract_id

        # Terminate contract
        contract.write({
            'end_reason': self.end_reason,
            'end_date': self.end_date,
            'transfer_partner_id': self.transfer_country_id.id,
        })
        contract.signal_workflow('contract_terminated')

        return True
