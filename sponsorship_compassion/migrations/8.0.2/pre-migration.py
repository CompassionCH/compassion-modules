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


def update_sequence_records(cr):
    """ Move partner sequence from ir_model_data. """
    cr.execute(
        "UPDATE ir_model_data "
        "SET module = 'sponsorship_compassion' "
        "WHERE model LIKE 'ir.sequence%' "
        "AND module = 'partner_compassion' ")


def migrate(cr, version):
    if not version:
        return

    # Change type of analytic accounts
    update_sequence_records(cr)
