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

from openerp.osv import orm, fields
from openerp.tools.translate import _
import logging

logger = logging.getLogger(__name__)


class recurring_invoicer_wizard(orm.TransientModel):
    ''' This wizard generate invoices from contracts when launched. By default, all contracts are used'''
    _name = 'recurring.invoicer.wizard'
    
    _columns = {
        'invoice_ids': fields.one2many('account.invoice', 'recurring_invoicer_id', _('Generated invoices'), readonly=True),
        'generation_date': fields.date(_('Generation date'), readonly=True),
        'group_invoices': fields.boolean(_('Group invoices'), help=_('If true, all invoice lines generated for a same customer \
            are grouped into the same invoice. Otherwise, an invoice is generated for each contract.')),
    }
    
    def generate(self, cr, uid, ids, context=None, group=True):
        contract_group_obj = self.pool.get('simple.recurring.contract.group')
        recurring_invoicer_obj = self.pool.get('recurring.invoicer')
        invoicer_id = recurring_invoicer_obj.create(cr, uid, {}, context)
        
        group_invoices = group
        if ids:
            form = self.browse(cr, uid, ids[0], context)
            group_invoices = form.group_invoices
        
        contract_group_obj.generate_invoices(cr, uid, [], invoicer_id, group_invoices, context)
        
        # If no invoice in invoicer, we raise and exception.
        # This will cancel the invoicer creation too !
        recurring_invoicer = recurring_invoicer_obj.browse(cr, uid, invoicer_id, context)
        if not recurring_invoicer.invoice_ids:
            raise orm.except_orm('ValueError', _('0 invoices have been generated.'))
        
        return {
            'name': 'recurring.invoicer.form',
            'view_mode': 'form',
            'view_type': 'form,tree',
            'res_id' : invoicer_id, # id of the object to which to redirect
            'res_model': 'recurring.invoicer', # object name
            'type': 'ir.actions.act_window',
        }
        
    def generate_from_cron(self, cr, uid, group=False, context=None):
        self.generate(cr, uid, [], context=context, group=group)
