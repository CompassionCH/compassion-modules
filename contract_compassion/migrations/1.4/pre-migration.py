# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Albert SHENOUDA <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
logger = logging.getLogger()


def update_analytic_accounts(cr):
    """ Change the type of the analytic accounts. """
    # Find all analytic accounts related to events
    cr.execute(
        "DELETE "
        "FROM ir.model.data "
        "WHERE model = 'product.template' AND module = 'contract_compassion' ")


def migrate(cr, version):
    if not version:
        return

    # Change type of analytic accounts
    update_analytic_accounts(cr)
