# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Move general fund product data
    openupgrade.rename_xmlids(
        cr,
        [('sponsorship_switzerland.product_template_fund_gen',
          'sponsorship_compassion.product_template_fund_gen')])
