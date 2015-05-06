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

from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

from lxml import etree
from datetime import datetime

from child_compassion.wizard.child_depart_wizard import IP_COUNTRIES


class end_contract_wizard(orm.TransientModel):
    _name = 'end.contract.wizard'

    def _get_contract_id(self, cr, uid, context=None):
        # Retrieve the id of the contract from context
        return context.get('active_id', False)

    def _get_child_id(self, cr, uid, context=None):
        # Retrieve the id of the sponsored child
        contract = self.pool.get('recurring.contract').browse(
            cr, uid, context.get('active_id'), context)
        return contract.child_id.id if contract.type == 'S' else False

    def _get_end_reason(self, cr, uid, context=None):
        return self.pool.get('recurring.contract').get_ending_reasons(
            cr, uid, context)

    _columns = {
        'end_date': fields.date(_('End date'), required=True),
        'contract_id': fields.many2one('recurring.contract', 'Contract'),
        'child_id': fields.many2one('compassion.child', 'Child'),
        'end_reason': fields.selection(_get_end_reason, string=_('End reason'),
                                       required=True),
        'do_transfer': fields.boolean(_("I want to transfer the child")),
        'transfer_country_id': fields.many2one(
            'res.country', _('Country'),
            domain=[('code', 'in', IP_COUNTRIES)]),
    }

    _defaults = {
        'contract_id': _get_contract_id,
        'child_id': _get_child_id,
        'end_date': datetime.today().strftime(DF),
    }

    def fields_view_get(self, cr, user, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(end_contract_wizard, self).fields_view_get(
            cr, user, view_id, view_type, context, toolbar, submenu)
        # If there is no child in contract, hide field
        if view_type == 'form' and not self._get_child_id(cr, user, context):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='child_id']"):
                node.set('invisible', "1")
                orm.setup_modifiers(node, res['fields']['child_id'])
            res['arch'] = etree.tostring(doc)

        return res

    def end_contract(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        contract = wizard.contract_id

        # Terminate contract
        contract.write({'end_reason': wizard.end_reason,
                        'end_date': wizard.end_date})

        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            uid, 'recurring.contract', contract.id, 'contract_terminated', cr)

        return True
