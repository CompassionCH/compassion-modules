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

from openerp.osv import orm, fields
from openerp.tools.translate import _
import pdb


class end_sponsorship_wizard(orm.TransientModel):
    _name = 'end.sponsorship.wizard'
        
    def _get_contract_id(self, cr, uid, context=None):
        # Retrieve the id of the contract from context
        return context.get('active_id', False)
    
    def _get_selection(self, cr, uid, context=None):
        return self.pool.get('recurring.contract').get_ending_reasons(cr, uid)
    
    _columns = {
        'end_date': fields.date(_('End date')),
        'contract_id': fields.many2one('recurring.contract', 'Contract'),
        'end_reason': fields.selection(_get_selection, string=_('End reason'))
    }
    
    _defaults = {
        'contract_id': _get_contract_id
    }
    
    def end_sponsorship(self, cr, uid, ids, context=None):
        # TODO : Implement better this method
        contract_obj = self.pool.get('recurring.contract')
        child_obj = self.pool.get('child.compassion')
        wizard = self.browse(cr, uid, ids[0], context)
        contract_id = wizard.contract_id.id
        contract_obj.write(cr, uid, contract_id, {'end_reason': wizard.end_reason}, context)
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'recurring.contract', contract_id, 'contract_terminated', cr, context)
        
        return True

    
