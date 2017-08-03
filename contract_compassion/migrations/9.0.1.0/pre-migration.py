# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Move data
    cr.execute("""
UPDATE ir_model_data SET module='sponsorship_switzerland'
WHERE module='contract_compassion' AND
  (name LIKE 'product_template_%' OR name LIKE 'payment_term_%');
    """)
