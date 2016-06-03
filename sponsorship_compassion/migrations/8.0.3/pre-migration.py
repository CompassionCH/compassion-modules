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
logger = logging.getLogger()


def migrate(cr, version):
    if not version:
        return

    # Move fields from module sbc_compassion
    cr.execute("""
UPDATE ir_model_data SET module='sponsorship_compassion'
WHERE name IN ('field_res_partner_send_original',
               'field_res_partner_mandatory_review');
    """)
