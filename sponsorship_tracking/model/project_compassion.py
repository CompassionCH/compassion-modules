##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp.osv import orm, fields
from openerp.tools.translate import _
import pdb

class compassion_project(orm.Model):
    _inherit = 'compassion.project'
    
    def project_terminated(self, cr, uid, project_id, context=None):
        self.write(cr, uid, project_id, {'status':'T'}, context)
        for contract in self._get_contracts(cr, uid, project_id, context):
            self.pool.get('recurring.contract').terminate_project(cr, uid, contract.id, context)
            
    def project_phase_out(self, cr, uid, project_id, context=None):
        self.write(cr, uid, project_id, {'status':'P'}, context)
        for contract in self._get_contracts(cr, uid, project_id, context):
            self.pool.get('recurring.contract').phase_out_project(cr, uid, contract.id, context)
        
    def project_fund_suspended(self, cr, uid, project_id, context=None):
        self.write(cr, uid, project_id, {'status':'S'}, context)  
        return
        
    def suspend_funds(self, cr, uid, project_id, context=None,
                      date_start=None, date_end=None):
        super(compassion_project, self).suspend_funds(cr, uid, project_id)
        self.project_fund_suspended(cr, uid, project_id)
        
        for contract in self._get_contracts(cr, uid, project_id, context):
            self.pool.get('recurring.contract').suspend_project(cr, uid, contract.id, context)
        
    def reactivate_project(self, cr, uid, project_id, context=None):
        super(compassion_project, self).reactivate_project(cr, uid, project_id, context)
        self.write(cr, uid, project_id, {'status': 'A'})

        for contract in self._get_contracts(cr, uid, project_id, context):
            self.pool.get('recurring.contract').reactivate_project(cr, uid, contract.id, context)

    def _get_contracts(self, cr , uid, project_id, context=None):
        contract_obj = self.pool.get('recurring.contract')
        contract_ids = contract_obj.search(cr, uid, [('project_id', '=', project_id)], context=context)
        return contract_obj.browse(cr, uid, contract_ids, context)
 
    def _get_state(self, cr, uid, context=None):
        res = super(compassion_project, self)._get_state(cr, uid, context)

        res[1:1] = [
            ('S',_('Fund suspended')),
        ]
        return res

    _columns = {
        'status': fields.selection(_get_state, _('Status'),
            track_visibility='onchange'),
    }