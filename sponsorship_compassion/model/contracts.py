# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp import netsvc
from openerp.tools.translate import _


class recurring_contract(orm.Model):
    _inherit = "recurring.contract"

    def _active(self, cr, uid, ids, field_name, args, context=None):
        # Dummy function that sets the active flag.
        self._on_contract_active(cr, uid, ids, context=context)
        return dict((id, True) for id in ids)

    def _get_contract_from_invoice(invoice_obj, cr, uid, invoice_ids,
                                   context=None):
        self = invoice_obj.pool.get('recurring.contract')
        res = []
        for invoice in invoice_obj.browse(cr, uid, invoice_ids,
                                          context=context):
            if invoice.state == 'paid':
                self._invoice_paid(cr, uid, invoice, context=context)
                for invoice_line in invoice.invoice_line:
                    contract = invoice_line.contract_id
                    if contract.state == 'waiting':
                        # We should activate the contract and set the
                        # first_payment_date
                        res.append(invoice_line.contract_id.id)
                        self.write(cr, uid, contract.id,
                                   {'first_payment_date':
                                    invoice.payment_ids[0].date},
                                   context=context)

        return res

    def _on_contract_active(self, cr, uid, ids, context=None):
        """ Hook for doing something when contract is activated. """
        wf_service = netsvc.LocalService('workflow')
        for id in ids:
            wf_service.trg_validate(uid, 'recurring.contract', id,
                                    'contract_active', cr)

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
        'child_id': fields.many2one(
            'compassion.child', _('Sponsored child'), readonly=True,
            states={'draft': [('readonly', False)]}),
        'child_name': fields.related(
            'child_id', 'name', string=_('Sponsored child name'),
            readonly=True, type='char'),
        'child_code': fields.related(
            'child_id', 'code', string=_('Sponsored child code'),
            readonly=True, type='char'),
        'partner_codega': fields.related(
            'partner_id', 'ref', string=_('Partner ref'), readonly=True,
            type='char'),
        # This field is only for the middleware testing purpose.
        # In the future, the type will be identified in another way.
        'type': fields.selection([
            ('ChildSponsorship', 'Sponsorship'),
            ('ChildCorrespondenceSponsorship', 'Correspondence')],
            _("Type of sponsorship")),
        'correspondant_id': fields.many2one(
            'res.partner', _('Correspondant'), required=True),
        'first_payment_date': fields.date(
            _('First payment date'), readonly=True),
        # Add a waiting state
        'state': fields.selection([
            ('draft', _('Draft')),
            ('waiting', _('Waiting Payment')),
            ('active', _('Active')),
            ('terminated', _('Terminated')),
            ('cancelled', _('Cancelled'))], _('Status'), select=True,
            readonly=True, track_visibility='onchange',
            help=_(" * The 'Draft' status is used when a user is encoding a "
                   "new and unconfirmed Contract.\n"
                   " * The 'Waiting' status is used when the Contract is "
                   " confirmed but the partner has not yet paid.\n"
                   " * The 'Active' status is used when the contract is "
                   "confirmed and until it's terminated.\n"
                   " * The 'Terminated' status is used when a contract is no "
                   "longer active.\n"
                   " * The 'Cancelled' status is used when a contract was "
                   "never paid.")),
        'is_active': fields.function(
            _active, string='Contract Active', type='boolean',
            store={
                'account.invoice': (_get_contract_from_invoice, ['state'], 50)
            },
            help="It indicates that the first invoice has been paid and the "
                 "contract is active."),
        'fully_managed': fields.function(
            _is_fully_managed, type="boolean", store=True),
        # Field used for identifying gifts from sponsor (because of bad GP)
        'num_pol_ga': fields.integer(
            'Partner Contract Number', required=True
        ),
    }

    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        ''' On partner change, we update the correspondent and 
        set the new pol_number (for gift identification).'''
        res = super(recurring_contract, self).on_change_partner_id(
            cr, uid, ids, partner_id, context)
        num_contracts = self.search(
            cr, uid, [('partner_id', '=', partner_id)], context=context,
            count=True)
        res['value'].update({
            'correspondant_id': partner_id,
            'num_pol_ga': num_contracts
        })
        return res

    def contract_waiting(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'waiting'})
        return True

    def contract_cancelled(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'cancelled'})
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        num_pol_ga = self.browse(cr, uid, id, context=context).num_pol_ga
        default.update({
            'child_id': False,
            'first_payment_date': False,
            'is_active': False,
            'num_pol_ga': num_pol_ga+1,
        })
        return super(recurring_contract, self).copy(cr, uid, id, default, context)

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        contracts = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []

        for t in contracts:
            # We can only delete draft contracts.
            if t['state'] != 'draft':
                raise orm.except_orm(_('Warning'),
                                     _('You cannot delete a contract that is '
                                       'still active. Terminate it first.'))
            else:
                unlink_ids.append(t['id'])

        super(recurring_contract, self).unlink(cr, uid, unlink_ids,
                                               context=context)
        return

    def write(self, cr, uid, ids, vals, context=None):
        """ Prevent to change next_invoice_date in the past. """
        if 'next_invoice_date' in vals:
            new_date = vals['next_invoice_date']
            for contract in self.browse(cr, uid, ids, context=context):
                if new_date < contract.next_invoice_date:
                    raise orm.except_orm(_('Warning'),
                                         _('You cannot rewind the next '
                                           'invoice date.'))

        return super(recurring_contract, self).write(cr, uid, ids, vals,
                     context=context)

    def validate_from_gp(self, cr, uid, ids, context=None):
        """ Used to transition draft sponsorships in waiting state 
        when exported from GP. """
        wf_service = netsvc.LocalService('workflow')
        for id in ids:
            wf_service.trg_validate(uid, 'recurring.contract', id,
                                    'contract_validated', cr)
        return True

    def activate_from_gp(self, cr, uid, ids, context=None):
        """ Used to transition draft sponsorships in active state 
        when exported from GP. """
        self.validate_from_gp(cr, uid, ids, context)
        self._on_contract_active(cr, uid, ids, context)
        return True

    def terminate_from_gp(self, cr, uid, ids, context=None):
        """ Used to delete the workflow of terminated or cancelled
        sponsorships when exported from GP. """
        wf_service = netsvc.LocalService('workflow')
        for id in ids:
            wf_service.trg_delete(uid, 'recurring.contract', id, cr)
        return True


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
    _inherit = 'recurring.contract.line'
