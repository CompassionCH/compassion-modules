# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
from openerp import models, api


logger = logging.getLogger(__name__)


class MigrationAnalytic(models.TransientModel):
    """ Perform migrations after upgrading the module
    """
    _name = 'migration.analytic'

    @api.model
    def perform_migration(self):
        # Only execute migration for 8.0.2 -> 8.0.2.5
        sponsorship_module = self.env['ir.module.module'].search([
            ('name', '=', 'sponsorship_compassion')
        ])
        if sponsorship_module.latest_version == '8.0.2':
            self._perform_migration()
        return True

    def _perform_migration(self):
        """
        Finds invoices that should have analytic line of origin
        """
        logger.info("MIGRATION : Putting analytic of origins in lines")
        contracts = self.env['recurring.contract'].search([
            ('origin_id.analytic_id', '!=', False)
        ])
        count = 1
        total = len(contracts)
        for contract in contracts:
            self.env.invalidate_all()
            logger.info("MIGRATION : Contract {} / {}".format(count, total))
            analytic = contract.origin_id.analytic_id
            invoice_lines = contract.invoice_line_ids.filtered(
                lambda invl: invl.product_id.name == 'Sponsorship' and
                invl.account_analytic_id != analytic)
            for invoice_line in invoice_lines:
                move_line = invoice_line.invoice_id.move_id.line_id.\
                    filtered(lambda mvl: mvl.account_id.code == '6000' and
                             mvl.analytic_account_id.name == 'Income')

                # Change analytic of invoice_line, move_line and analytic_line
                invoice_line.account_analytic_id = analytic
                if move_line:
                    move_line[0].analytic_account_id = analytic
                    analytics = move_line[0].analytic_lines.filtered(
                        lambda al: al.account_id.name == 'Income')
                    if analytics:
                        analytics.account_id = analytic

            # Commit after each contract done
            self.env.cr.commit()
            count += 1
