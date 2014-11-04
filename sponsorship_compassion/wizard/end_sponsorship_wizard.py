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

# Countries available for the child transfer
IP_COUNTRIES = ['AU', 'CA', 'DE', 'ES', 'FR', 'GB', 'IT', 'KR', 'NL',
                'NZ', 'US']


class end_sponsorship_wizard(orm.TransientModel):
    _name = 'end.sponsorship.wizard'

    def _get_contract_id(self, cr, uid, context=None):
        # Retrieve the id of the contract from context
        return context.get('active_id', False)

    def _get_child_id(self, cr, uid, context=None):
        # Retrieve the id of the sponsored child
        contract = self.pool.get('recurring.contract').browse(
            cr, uid, context.get('active_id'), context)
        return contract.child_id.id if contract.child_id else False

    def _get_end_reason(self, cr, uid, context=None):
        return self.pool.get('recurring.contract').get_ending_reasons(cr, uid)
        
    def _get_exit_reason(self, cr, uid, context=None):
        return self.pool.get('compassion.child').get_gp_exit_reasons(cr, uid)

    _columns = {
        'end_date': fields.date(_('End date'), required=True),
        'contract_id': fields.many2one('recurring.contract', 'Contract'),
        'child_id': fields.many2one('compassion.child', 'Child'),
        'end_reason': fields.selection(_get_end_reason, string=_('End reason'),
                                       required=True),
        'state': fields.selection(
            [('end_sponsorship', 'End Sponsorship'),
             ('transfer_child', 'Transfer Child'),
             ('exit_details', 'Child Exit Details')],
            'State', required=True, readonly=True),
        'do_transfer': fields.boolean(_("I want to transfer the child")),
        'transfer_country_id': fields.many2one(
            'res.country', _('Country'),
            domain=[('code', 'in', IP_COUNTRIES)]),
        'gp_exit_reason': fields.selection(_get_exit_reason, string=_('Exit reason')),
    }

    _defaults = {
        'state': 'end_sponsorship',
        'contract_id': _get_contract_id,
        'child_id': _get_child_id,
        'end_date': datetime.today().strftime(DF),
    }

    def fields_view_get(self, cr, user, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(end_sponsorship_wizard, self).fields_view_get(
            cr, user, view_id, view_type, context, toolbar, submenu)
        # If there is no child in contract, hide field
        if view_type == 'form' and not self._get_child_id(cr, user, context):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='child_id']"):
                node.set('invisible', "1")
                orm.setup_modifiers(node, res['fields']['child_id'])
            res['arch'] = etree.tostring(doc)

        return res

    def end_sponsorship(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        res = True

        if wizard.child_id:
            child_update = {'sponsor_id': False}

            # If sponsor moves, propose to transfer the child
            if wizard.end_reason == '4':
                wizard.write({'state': 'transfer_child'})
                res = {
                    'name': _('Transfer child to another country'),
                    'type': 'ir.actions.act_window',
                    'res_model': self._name,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_id': ids[0],
                    'context': context,
                    'target': 'new',
                }

            # If child has departed, go to exit_details step
            elif wizard.end_reason == '1':
                wizard.write({'state': 'exit_details'})
                res = {
                    'name': _('Child exit details'),
                    'type': 'ir.actions.act_window',
                    'res_model': self._name,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_id': ids[0],
                    'context': context,
                    'target': 'new',
                }

            wizard.child_id.write(child_update)

        contract = wizard.contract_id
        contract.write({'end_reason': wizard.end_reason})
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            uid, 'recurring.contract', contract.id, 'contract_terminated', cr)

        return res

    def transfer_child(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        if wizard.do_transfer and wizard.transfer_country_id:
            wizard.child_id.write({
                'state': 'F',
                'transfer_country_id': wizard.transfer_country_id.id})

        return True
        
    def depart_child(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        wizard.child_id.write({
            'state': 'F',
            'gp_exit_reason': wizard.gp_exit_reason,
        })
        return True
