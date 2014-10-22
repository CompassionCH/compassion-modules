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

from . import gp_connector


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
        res = super(contracts, self).write(cr, uid, ids, vals, context)
        gp_connect = gp_connector.GPConnect(cr, uid)
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
            synced = gp_connect.cancel_contract(contract.id)
            super(contracts, self).write(cr, uid, contract.id, {'synced_with_gp': synced},
                                         context)
        return True

    def contract_terminated(self, cr, uid, ids, context=None):
        """ When contract is terminated, update it in GP. """
        super(contracts, self).contract_cancelled(cr, uid, ids)
        gp_connect = gp_connector.GPConnect(cr, uid)
        for contract in self.browse(cr, uid, ids, context):
            synced = gp_connect.finish_contract(contract.id)
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
        """ When an invoice is paid, update last payment date in GP. """
        gp_connect = gp_connector.GPConnect(cr, uid)
        last_pay_date = max([move_line.date
                             for move_line in invoice.payment_ids
                             if move_line.credit > 0])
        for line in invoice.invoice_line:
            contract = line.contract_id
            if contract:
                synced = gp_connect.register_payment(
                    contract.id, last_pay_date)
                super(contracts, self).write(cr, uid, contract.id, {'synced_with_gp': synced},
                           context)

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
