# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Albert SHENOUDA <albert.shenouda@efrei.net>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.tests import common
from datetime import datetime
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import logging
logger = logging.getLogger(__name__)


class test_crm_compassion(common.TransactionCase):

    def setUp(self):
        super(test_crm_compassion, self).setUp()
        # Retrieve receivable and payable accounts
        account_type = self.registry('account.account.type').search(
            self.cr, self.uid, [
                ('code', '=', 'receivable'),
            ])[0]
        property_account_receivable = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'receivable'),
                ('user_type', '=', account_type)
            ])[0]
        account_type = self.registry('account.account.type').search(
            self.cr, self.uid, [
                ('code', '=', 'payable'),
            ])[0]
        property_account_payable = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'payable'),
                ('user_type', '=', account_type)])[0]
        property_account_income = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'other'),
                ('name', '=', 'Property Account Income Test')
            ])[0]
        property_account_expense = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'other'),
                ('name', '=', 'Property Account Expense Test')
            ])[0]
        # Creation of partners
        partner_obj = self.registry('res.partner')
        self.partner_id = partner_obj.create(self.cr, self.uid, {
            'name': 'Monsieur Bryan',
            'property_account_receivable': property_account_receivable,
            'property_account_payable': property_account_payable,
            'notification_email_send': 'comment',
        })
        self.admin_id = self.registry('res.users').search(
            self.cr, self.uid, [('name', '=', 'Administrator')])[0]
        self.partner_id2 = self.registry('res.partner').search(
            self.cr, self.uid, [('name', '=', 'Michel Fletcher')])[0]
        # Retrieve a payment term
        payment_term_obj = self.registry('account.payment.term')
        self.payment_term_id = payment_term_obj.search(self.cr, self.uid, [
            ('name', '=', '15 Days')
        ])[0]
        # Retrieve and modification of products
        product_obj = self.registry('product.product')
        product_sp_id = product_obj.search(
            self.cr, self.uid, [('name', '=', 'Sponsorship')])[0]
        product_gf_id = product_obj.search(
            self.cr, self.uid, [('name', '=', 'General Fund')])[0]
        product_bf_id = product_obj.search(
            self.cr, self.uid, [('name', '=', 'Birthday Gift')])[0]
        product_fg_id = product_obj.search(
            self.cr, self.uid, [('name', '=', 'Family Gift')])[0]
        product_obj.write(self.cr, self.uid, product_sp_id, {
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
            })
        product_obj.write(self.cr, self.uid, product_gf_id, {
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
        })
        product_obj.write(self.cr, self.uid, product_bf_id, {
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
        })
        product_obj.write(self.cr, self.uid, product_fg_id, {
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
        })

    def test_crm_compassion(self):
        """
            This scenario consists in the creation of an opportunity,
            then comes the event. Check if the project which is created from
            the event has coherent data with the event.
            Check if we can find the origin from the event in a sponsorship
            contract.
        """

        # Creation of a lead and an event
        lead_id = self._create_lead(
            'PlayoffsCompassion', self.admin_id)
        lead_id2 = self._create_lead(
            'JO_Compassion', self.admin_id)
        self.assertTrue(lead_id)
        event_id = self._create_event(lead_id)
        event_id2 = self._create_event(lead_id2)
        self.assertTrue(event_id)
        event = self.registry('crm.event.compassion').browse(
            self.cr, self.uid, event_id)
        event.write({'use_tasks': True, 'partner_id': self.partner_id})
        event = self.registry('crm.event.compassion').browse(
            self.cr, self.uid, event_id)
        event2 = self.registry('crm.event.compassion').browse(
            self.cr, self.uid, event_id2)
        event2.write({'use_tasks': True, 'partner_id': self.partner_id})
        self.assertTrue(event.project_id)

        # Retrieve of the project from the event
        project = self.registry('project.project').browse(
            self.cr, self.uid, event.project_id.id)

        # Creation of a marketing project and check if an origin is created
        self._create_project(
            'Marketing Project', 'employees', self.admin_id, 'marketing', True)
        mark_origin = self.registry('recurring.contract.origin').search(
            self.cr, self.uid, [('type', '=', 'marketing')])
        self.assertTrue(mark_origin)
        self.assertEqual(project.date_start, event.start_date[:10])
        self.assertEqual(project.analytic_account_id, event.analytic_id)
        self.assertEqual(project.project_type, event.type)
        self.assertEqual(project.user_id, event.user_id)
        self.assertEqual(project.name, event.name)

        # Create a child and get the project associated
        child_id = self._create_child('PE3760136')
        child = self.registry('compassion.child').browse(
            self.cr, self.uid, child_id)
        child.get_infos()
        child.project_id.write({'disburse_funds': True})

        # Creation of the sponsorship contract
        sp_group = self._create_group(
            'do_nothing', self.partner_id, 1, self.payment_term_id)
        sponsorship_id = self._create_sponsorship(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF), 'postal', 'S',
            child_id, event_id)
        contract_obj = self.registry('recurring.contract')
        sponsorship = contract_obj.browse(
            self.cr, self.uid, sponsorship_id)
        sponsorship.write({'user_id': self.partner_id2})
        self.assertEqual(sponsorship.origin_id.name, event.full_name)
        self.assertEqual(sponsorship.state, 'draft')
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id, 'contract_validated', self.cr)
        sponsorship = contract_obj.browse(
            self.cr, self.uid, sponsorship_id)
        invoicer_obj = self.registry('recurring.invoicer')
        invoicer_id = sponsorship.button_generate_invoices()
        invoices = invoicer_obj.browse(
            self.cr, self.uid, invoicer_id).invoice_ids
        self.assertEqual(len(invoices), 2)
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(
            invoices[0].invoice_line[0].user_id, sponsorship.user_id)
        partner = self.registry('res.partner').browse(
            self.cr, self.uid, self.partner_id)
        event_dico = partner.open_events()
        self.assertEqual(len(event_dico['domain'][0][2]), 2)

    def _create_project(self, name, privacy_visibility, user_id, type, bool):
        project_id = self.registry('project.project').create(
            self.cr, self.uid, {
                'name': name,
                'privacy_visibility': privacy_visibility,
                'user_id': user_id,
                'project_type': type,
                'use_tasks': bool,
                'date_start': datetime.today().strftime(DF),
            })
        return project_id

    def _create_event(self, lead_id):
        lead = self.registry('crm.lead').browse(self.cr, self.uid, lead_id)
        event_dico = lead.create_event(context={})
        event_id = self.registry('crm.event.compassion').create(
            self.cr, self.uid, {
                'name': event_dico['context']['default_name'],
                'type': 'sport',
                'start_date': datetime.today().strftime(DF),
                'lead_id': lead_id,
                'user_id': event_dico['context']['default_user_id'],
                'parent_id': 7,
            })
        return event_id

    def _create_lead(self, name, user_id):
        lead_id = self.registry('crm.lead').create(
            self.cr, self.uid, {
                'name': name,
                'user_id': user_id,
            })
        return lead_id

    def _create_sponsorship(self, start_date, group_id, next_invoice_date,
                            channel, type, child_id, event_id):
        group = self.registry('recurring.contract.group').browse(
            self.cr, self.uid, group_id)
        partner_id = group.partner_id.id
        event = self.registry('crm.event.compassion').browse(
            self.cr, self.uid, event_id)
        sponsorship_id = self.registry('recurring.contract').create(
            self.cr, self.uid, {
                'start_date': start_date,
                'partner_id': partner_id,
                'correspondant_id': partner_id,
                'group_id': group_id,
                'next_invoice_date': next_invoice_date,
                'origin_id': event.origin_id.id,
                'channel': channel,
                'type': type,
                'child_id': child_id,
            }, {'default_type': type})
        return sponsorship_id

    def _create_group(self, change_method, partner_id, adv_biling_months,
                      payment_term_id):
        """
            Create a group with 2 possibilities :
                - ref is not given so it takes "/" default values
                - ref is given
        """
        group_obj = self.registry('recurring.contract.group')
        group_id = group_obj.create(self.cr, self.uid, {
            'partner_id': partner_id,
        })
        group = group_obj.browse(self.cr, self.uid, group_id)
        group_vals = {
            'change_method': change_method,
            'partner_id': partner_id,
            'advance_billing_months': adv_biling_months,
            'payment_term_id': payment_term_id,
        }
        group.write(group_vals)
        return group_id

    def _create_child(self, code):
        child_id = self.registry('compassion.child').create(
            self.cr, self.uid, {
                'code': code,
            })
        return child_id

    def _pay_invoice(self, invoice_id):
        journal_obj = self.registry('account.journal')
        bank_journal_id = self.registry('account.journal').search(
            self.cr, self.uid, [('code', '=', 'TBNK')])[0]
        bank_journal = journal_obj.browse(self.cr, self.uid, bank_journal_id)
        move_obj = self.registry('account.move')
        move_line_obj = self.registry('account.move.line')
        invoice = self.registry('account.invoice').browse(
            self.cr, self.uid, invoice_id)
        account_id = invoice.partner_id.property_account_receivable.id
        move_id = move_obj.create(self.cr, self.uid, {
            'journal_id': bank_journal_id
        })
        move_line_obj.create(self.cr, self.uid, {
            'name': 'BNK-' + invoice.number,
            'move_id': move_id,
            'partner_id': invoice.partner_id.id,
            'account_id': bank_journal.default_debit_account_id.id,
            'debit': invoice.amount_total,
            'journal_id': bank_journal_id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_due
        })
        mv_line_id = move_line_obj.create(self.cr, self.uid, {
            'name': 'PAY-' + invoice.number,
            'move_id': move_id,
            'partner_id': invoice.partner_id.id,
            'account_id': account_id,
            'credit': invoice.amount_total,
            'journal_id': invoice.journal_id.id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_due
        })
        move_obj.button_validate(self.cr, self.uid, [move_id])
        to_reconcile = move_line_obj.search(self.cr, self.uid, [
            ('move_id', '=', invoice.move_id.id),
            ('account_id', '=', account_id)]) + [mv_line_id]
        move_line_obj.reconcile(self.cr, self.uid, to_reconcile)
