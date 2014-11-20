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

from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp import netsvc

from datetime import datetime
from dateutil.relativedelta import relativedelta


class project_compassion(orm.Model):
    _inherit = 'compassion.project'

    def suspend_project_from_gp(self, cr, uid, project_id, start, months,
                                context=None):
        date_start = datetime.strptime(start, DF)
        date_end = date_start + relativedelta(months=months)
        project = self.browse(cr, uid, project_id, context)
        contract_obj = self.pool.get('recurring.contract')
        contract_ids = contract_obj.search(
            cr, uid, [('child_code', 'like', project.code),
                      ('state', 'in', ('active', 'waiting'))], context=context)
        invl_obj = self.pool.get('account.invoice.line')
        inv_line_ids = invl_obj.search(cr, uid, [
            ('contract_id', 'in', contract_ids),
            ('state', 'in', ('open', 'paid')),
            ('due_date', '>=', date_start.strftime(DF)),
            ('due_date', '<', date_end.strftime(DF))], context=context)
        inv_ids = set()
        # Cancel invoices in the period of suspension
        for inv_line in invl_obj.browse(cr, uid, inv_line_ids, context):
            invoice = inv_line.invoice_id
            if invoice.id not in inv_ids:
                inv_ids.add(invoice.id)
                if invoice.state == 'paid':
                    # Unreconcile entries
                    move_ids = [move.id for move in invoice.payment_ids]
                    self.pool.get('account.move.line')._remove_move_reconcile(
                        cr, uid, move_ids, context=context)
                    cr.commit()
                # Cancel invoice
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_validate(uid, 'account.invoice', invoice.id,
                                        'invoice_cancel', cr)
        # Advance next invoice date after end of suspension
        for contract in contract_obj.browse(cr, uid, contract_ids, context):
            next_inv_date = datetime.strptime(contract.next_invoice_date, DF)
            month_diff = relativedelta(date_end, next_inv_date).months
            if month_diff > 0:
                # If sponsorship is late, don't advance it too much
                if month_diff > months:
                    month_diff = months
                new_date = next_inv_date + relativedelta(months=month_diff)
                contract.write({'next_invoice_date': new_date.strftime(DF)})

            # Add a note in the contract
            self.pool.get('mail.thread').message_post(
                cr, uid, contract.id,
                "The project {0} was suspended and funds are retained <b>"
                "until {1}</b>.<br/>Invoices due in the suspension period "
                "are automatically cancelled.".format(
                    project.code, date_end.strftime("%B %Y")),
                "Project Suspended", 'comment',
                context={'thread_model': 'recurring.contract'})

        return True
