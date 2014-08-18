# -*- encoding: utf-8 -*-
##############################################################################
#
#    Recurring contract module for openERP
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    @author: Cyril Sester <csester@compassion.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
        contract_obj = self.pool.get('simple.recurring.contract')
        recurring_invoicer_obj = self.pool.get('recurring.invoicer')
        invoicer_id = recurring_invoicer_obj.create(cr, uid, {}, context)
        
        group_invoices = group
        if ids:
            form = self.browse(cr, uid, ids[0], context)
            group_invoices = form.group_invoices
        
        contract_obj.generate_invoices(cr, uid, [], invoicer_id, group_invoices, context)
        
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
    
recurring_invoicer_wizard()