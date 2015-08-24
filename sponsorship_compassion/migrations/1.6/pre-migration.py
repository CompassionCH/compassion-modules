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


def update_product_records(cr):
    """ Remove ir_model_data to avoid product deletion. """
    cr.execute(
        "DELETE FROM ir_model_data "
        "WHERE model = 'product.product' AND module = 'sponsorship_compassion' ")


def migrate(cr, version):
    if not version:
        return

    # Change type of analytic accounts
    update_product_records(cr)
