# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Cyril Sester. Copyright Compassion Suisse
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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import orm, fields
from openerp import netsvc
from openerp.tools import mod10r
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import pdb
import logging
import time

logger = logging.getLogger(__name__)

class simple_recurring_contract(orm.Model):
    _name = "simple.recurring.contract"
    _inherit = "simple.recurring.contract"
    
    def _active(self, cr, uid, ids, field_name, args, context=None):
        # Dummy function that sets the active flag.
        self._on_contract_active(cr, uid, ids, context=context)
        return dict((id, True) for id in ids)
        
    def _get_contract_from_invoice(invoice_obj, cr, uid, invoice_ids, context=None):
        self = invoice_obj.pool.get('simple.recurring.contract')
        res = []
        for invoice in invoice_obj.browse(cr, uid, invoice_ids, context=context):
            if invoice.state == 'paid':
                self._invoice_paid(cr, uid, invoice, context=context)
                for invoice_line in invoice.invoice_line:
                    contract = invoice_line.contract_id
                    if contract.state == 'waiting':
                        # We should activate the contract and set the first_payment_date
                        res.append(invoice_line.contract_id.id)
                        self.write(cr, uid, contract.id, {'first_payment_date' : invoice.payment_ids[0].date},
                                   context=context)
        
        return res
        
    def _on_contract_active(self, cr, uid, ids, context=None):
        """ Hook for doing something when contract is activated. """
        wf_service = netsvc.LocalService('workflow')
        for id in ids:
            wf_service.trg_validate(uid, 'simple.recurring.contract', id, 'contract_active', cr)
    
    def _invoice_paid(self, cr, uid, invoice, context=None):
        """ Hook for doing something when an invoice line is paid. """
        pass
        
    def _is_fully_managed(self, cr, uid, ids, field_name, arg, context):
        # Tells if the correspondant and the payer is the same person.
        res = {}
        for contract in self.browse(cr, uid, ids, context=context):
            res[contract.id] = contract.partner_id == contract.correspondant_id
        return res

    _columns = {
        'child_id' : fields.many2one('compassion.child', _('Sponsored child'), readonly=True, states={'draft':[('readonly',False)]}),
        'child_name': fields.related('child_id', 'name', string=_('Sponsored child name'), readonly=True, type='char'),
        'child_code': fields.related('child_id', 'code', string=_('Sponsored child code'), readonly=True, type='char'),
        'partner_codega': fields.related('partner_id', 'ref', string=_('Partner ref'), readonly=True, type='char'),
        # This field is only for the middleware testing purpose. In the future, the type will be identified in another way.
        'type' : fields.selection((('ChildSponsorship','Sponsorship'),('ChildCorrespondenceSponsorship','Correspondence')), _("Type of sponsorship")),
        'correspondant_id' : fields.many2one('res.partner', _('Correspondant'), readonly=True, states={'draft':[('readonly',False)]}),
        'first_payment_date' : fields.date(_('First payment date'), readonly=True),
        # Add a waiting state
        'state': fields.selection([
            ('draft', _('Draft')),
            ('waiting', _('Waiting Payment')),
            ('active', _('Active')),
            ('terminated', _('Terminated')),
            ('cancelled', _('Cancelled')),
            ], _('Status'), select=True, readonly=True, track_visibility='onchange',
            help=_(' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Contract.\n' \
                    ' * The \'Waiting\' status is used when the Contract is confirmed but the partner has not yet paid.\n' \
                    '* The \'Active\' status is used when the contract is confirmed and until it\'s terminated.\n' \
                    '* The \'Terminated\' status is used when a contract is no longer active.\n' \
                    '* The \'Cancelled\' status is used when a contract was never paid.')),
        'is_active': fields.function(_active, string='Contract Active', type='boolean',
            store={
                'account.invoice': (_get_contract_from_invoice, ['state'], 50),
            }, help="It indicates that the first invoice has been paid and the contract is active."),
        'fully_managed': fields.function(_is_fully_managed, type="boolean", store=True),
    }
        
    def contract_waiting(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'waiting'})
        return True
        
    def contract_cancelled(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'cancelled'})
        return True

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        contracts = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []

        for t in contracts:
            # We can only delete draft contracts.
            if t['state'] != 'draft':
                raise openerp.exceptions.Warning(_('You cannot delete a contract that is still active. Terminate it first.'))
            else:
                unlink_ids.append(t['id'])

        super(simple_recurring_contract, self).unlink(cr, uid, unlink_ids, context=context)
        return 

        
# just to modify access rights...
class recurring_invoicer(orm.Model):
    _inherit = 'recurring.invoicer'
    _name = 'recurring.invoicer'
    
class account_invoice(orm.Model):
    _inherit = 'account.invoice'
    _name = 'account.invoice'

class compassion_child(orm.Model):
    _inherit = 'compassion.child'

class compassion_project(orm.Model):
    _inherit = 'compassion.project'

class contract_line(orm.Model):
    _inherit = 'simple.recurring.contract.line'
