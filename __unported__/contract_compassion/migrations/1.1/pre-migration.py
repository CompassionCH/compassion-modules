# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
logger = logging.getLogger()


def migrate(cr, version):
    if not version:
        return

    # Move payment terms data to contract_compassion module
    cr.execute(
        """
        UPDATE ir_model_data
        SET module='contract_compassion'
        WHERE module='sponsorship_compassion' AND
        model IN('account.payment.term', 'account.payment.term.line')
        """
    )
