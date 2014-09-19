# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from datetime import datetime
from openerp.osv import osv, orm, fields
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
import logging

logger = logging.getLogger(__name__)

class recurring_invoicer(orm.Model):
    _name = 'recurring.invoicer'
    _rec_name = 'identifier'

    _columns = {
        'identifier': fields.char(_('Identifier'), required=True),
        'generation_date': fields.date(_('Generation date')),
        'invoice_ids': fields.one2many('account.invoice', 'recurring_invoicer_id', _('Generated invoices')),
    }
    
    _defaults = {
        'identifier': lambda self,cr,uid,context: self.pool.get('ir.sequence').next_by_code(
                cr, uid, 'rec.invoicer.ident', context=context),
        'generation_date': lambda self,cr,uid,context: datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT),
    }
        
    def validate_invoices(self, cr, uid, ids, context=None):
        ''' Validates created invoices (set state from draft to open)'''
        #Setup a popup message ?
        inv_obj = self.pool.get('account.invoice')
        
        invoice_ids = inv_obj.search(cr, uid, [('recurring_invoicer_id', '=', ids[0]), ('state', '=', 'draft')], context=context)

        if not invoice_ids:
            raise osv.except_osv(_('There is no invoice to validate'), '')
            return True

        wf_service = netsvc.LocalService('workflow')            
        for invoice in inv_obj.browse(cr, uid, invoice_ids, context):
            wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
        
        return True
    
    #When an invoice is cancelled, should we adjust next_invoice_date in contract ?
    def cancel_invoices(self, cr, uid, ids, context=None):
        ''' Cancel created invoices (set state from open to cancelled)'''
        inv_obj = self.pool.get('account.invoice')
        
        invoice_ids = inv_obj.search(cr, uid, [('recurring_invoicer_id', '=', ids[0]), ('state', '!=', 'cancel')], context=context)
        
        if not invoice_ids:
            raise osv.except_osv(_('There is no invoice to cancel'), '')
            return True
            
        wf_service = netsvc.LocalService('workflow')                        
        for invoice in inv_obj.browse(cr, uid, invoice_ids, context):
            wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_cancel', cr)         
        
        return True        
        
    def recreate(self, cr, uid, ids, context=None):
        ''' Delete/Cancels all invoices created during a run and regenerate them.
            If invoices have been validated, they are cancelled. Otherwise they are deleted.'''
        return True