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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime
from dateutil import relativedelta

from . import gp_connector
import pdb


class contracts(orm.Model):
    _inherit = 'recurring.contract'

    _columns = {
        'synced_with_gp': fields.boolean(_("Synchronized with GP"),
                                         help=_("Indicates if the contract "
                                                "is correctly updated in GP."),
                                         readonly=True),
    }

    def create(self, cr, uid, vals, context=None):
        """ When contract is created, push it to GP so that the mailing
        module can access all information. """
        contract_id = super(contracts, self).create(cr, uid, vals, context)
        gp_connect = gp_connector.GPConnect(cr, uid)
        contract = self.browse(cr, uid, contract_id, context)
        # Check that the contract is compatible with GP
        # (= only sponsorship and/or fund products, nothing else)
        compatible, no_link_whith_gp = self._is_gp_compatible(contract)
        if compatible:
            if gp_connect.create_or_update_contract(uid, contract):
                super(contracts, self).write(cr, uid, contract.id, {'synced_with_gp': True},
                           context)
        else:
            # Raise error only if one line of contract should have a link
            # with GP.
            if not no_link_whith_gp:
                raise orm.except_orm(
                    _("Not compatible with GP"),
                    _("You selected some products that are not available "
                      "in GP. You cannot create this contract.")
                )
        return contract_id
        
    def write(self, cr, uid, ids, vals, context=None):
        """ Keep GP updated when a contract is modified. """
        gp_connect = gp_connector.GPConnect(cr, uid)
        
        # If we change the next invoice date, we update GP
        if vals.get('next_invoice_date'):
            new_date = datetime.strptime(vals['next_invoice_date'], DF)
            for contract in self.browse(cr, uid, ids, context=context):
                old_date = datetime.strptime(contract.next_invoice_date, DF)
                month_diff = relativedelta.relativedelta(new_date, old_date).months
                if contract.state in ('active', 'waiting') and month_diff > 0:
                    if not gp_connect.register_payment(contract.id, amount=month_diff):
                        raise orm.except_orm(
                            _("GP Sync Error"),
                            _("The cancellation could not be registered "
                              "into GP. Please contact an IT person."))
                    
        res = super(contracts, self).write(cr, uid, ids, vals, context)
        ids = [ids] if not isinstance(ids, list) else ids
        for contract in self.browse(cr, uid, ids, context):
            compatible, no_link_whith_gp = self._is_gp_compatible(contract)
            if compatible:
                synced = gp_connect.create_or_update_contract(uid, contract)
                super(contracts, self).write(cr, uid, contract.id, {'synced_with_gp': synced},
                                   context)
            elif not no_link_whith_gp:
                raise orm.except_orm(
                    _("Not compatible with GP"),
                    _("You selected some products that are not available "
                      "in GP. You cannot save this contract.")
                )
            else:
                super(contracts, self).write(cr, uid, contract.id, {'synced_with_gp': False},
                                   context)

        return res
        
    def _is_gp_compatible(self, contract):
        """ Tells if the contract is compatible with GP and if the contract
        has a link with GP.
        Returns : - bool : is compatible with GP
                  - bool : the contract has to be exported in GP
        """
        compatible = True
        no_link_whith_gp = True
        for line in contract.contract_line_ids:
            compatible = compatible and (
                'Sponsorship' in line.product_id.name
                or line.product_id.gp_fund_id > 0)
            no_link_whith_gp = (
                no_link_whith_gp
                and 'Sponsorship' not in line.product_id.name
                and line.product_id.gp_fund_id == 0)
        return compatible, no_link_whith_gp
    
    def contract_waiting(self, cr, uid, ids, context=None):
        """ When contract is validated, calculate which month is due
        and push it to GP.
        """
        super(contracts, self).write(cr, uid, ids, {'state': 'waiting'}, context)
        gp_connect = gp_connector.GPConnect(cr, uid)
        for contract in self.browse(cr, uid, ids, context):
            if not contract.synced_with_gp:
                raise orm.except_orm(
                    _("Not synchronized with GP"),
                    _("The contract is not synchronized with GP. Please edit "
                      "it before validating."))
            synced = gp_connect.validate_contract(contract)
            super(contracts, self).write(cr, uid, contract.id, {'synced_with_gp': synced},
                       context)
        return True

    def contract_cancelled(self, cr, uid, ids, context=None):
        """ When contract is cancelled, update it in GP. """
        super(contracts, self).contract_cancelled(cr, uid, ids, context)
        gp_connect = gp_connector.GPConnect(cr, uid)
        for contract in self.browse(cr, uid, ids, context):
            synced = gp_connect.finish_contract(contract)
            super(contracts, self).write(cr, uid, contract.id, {'synced_with_gp': synced},
                                         context)
        return True

    def contract_terminated(self, cr, uid, ids, context=None):
        """ When contract is terminated, update it in GP. """
        super(contracts, self).contract_terminated(cr, uid, ids)
        gp_connect = gp_connector.GPConnect(cr, uid)
        for contract in self.browse(cr, uid, ids, context):
            synced = gp_connect.finish_contract(contract)
            super(contracts, self).write(cr, uid, contract.id, {'synced_with_gp': synced},
                                         context)
        return True

    def _on_contract_active(self, cr, uid, ids, context=None):
        """ When contract is active, update it in GP. """
        super(contracts, self)._on_contract_active(cr, uid, ids, context)
        gp_connect = gp_connector.GPConnect(cr, uid)
        for contract in self.browse(cr, uid, ids, context):
            synced = gp_connect.activate_contract(contract)
            super(contracts, self).write(cr, uid, contract.id, {'synced_with_gp': synced},
                       context)

    def _invoice_paid(self, cr, uid, invoice, context=None):
        """ When a customer invoice is paid, synchronize GP. """
        super(contracts, self)._invoice_paid(cr, uid, invoice, context)
        if invoice.type == 'out_invoice':
            gp_connect = gp_connector.GPConnect(cr, uid)
            last_pay_date = max([move_line.date
                                 for move_line in invoice.payment_ids
                                 if move_line.credit > 0] or [False])
            contract_ids = set()
            for line in invoice.invoice_line:
                gp_connect.insert_affectat(uid, line, last_pay_date)
                contract = line.contract_id
                if contract:
                    if line.product_id.name == 'Standard Sponsorship' and not contract.id in contract_ids:
                        if not gp_connect.register_payment(contract.id, last_pay_date):
                            raise orm.except_orm(
                                _("GP Sync Error"),
                                _("The payment could not be registered into GP. "
                                  "Please contact an IT person."))
                        contract_ids.add(contract.id)

    def _invoice_open(self, cr, uid, invoice, context=None):
        """ If an invoice that was paid is set back to open state,
        remove the payment lines in GP. """
        super(contracts, self)._invoice_open(cr, uid, invoice, context)
        last_pay_date = max([move_line.date
                                 for move_line in invoice.payment_ids
                                 if move_line.credit > 0] or [False])
        pdb.set_trace()
        was_paid = ['Invoice paid' in m.description for m in invoice.message_ids]
        if invoice.type == 'out_invoice' and was_paid: # TODO NOT WORKING
            gp_connect = gp_connector.GPConnect(cr, uid)
            gp_connect.remove_affectat(invoice.id, last_pay_date)
            
            contract_ids = set()
            for line in invoice.invoice_line:
                contract = line.contract_id
                if contract and contract.id not in contract_ids:
                    contract_ids.add(contract.id)
                    if not gp_connect.undo_payment(contract.id):
                        raise orm.except_orm(
                                _("GP Sync Error"),
                                _("The payment could not be removed from GP. "
                                  "Please contact an IT person."))
    
    def _invoice_cancel(self, cr, uid, invoice, context=None):        
        """ If an invoice was cancelled, update the situation in GP. """
        super(contracts, self)._invoice_cancel(cr, uid, invoice, context)
        if invoice.type == 'out_invoice' and invoice.move_id:
            contract_ids = set()
            gp_connect = gp_connector.GPConnect(cr, uid)
            for line in invoice.invoice_line:
                contract = line.contract_id
                if contract and contract.id not in contract_ids:
                    contract_ids.add(contract.id)
                    if not gp_connect.register_payment(line.contract_id.id):
                        raise orm.except_orm(
                            _("GP Sync Error"),
                            _("The cancellation could not be registered "
                              "into GP. Please contact an IT person."))

class contract_group(orm.Model):
    """ Update all contracts when group is changed. """
    _inherit = 'recurring.contract.group'
    
    def write(self, cr, uid, ids, vals, context=None):
        res = super(contract_group, self).write(cr, uid, ids, vals, context)
        gp_connect = gp_connector.GPConnect(cr, uid)
        for group in self.browse(cr, uid, ids, context):
            for contract in group.contract_ids:
                gp_connect.create_or_update_contract(uid, contract)
        return res
