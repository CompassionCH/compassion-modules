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


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        UPDATE recurring_contract
        SET sds_state_date = sds_state_date_old
        """)
    cr.execute(
        """
        ALTER TABLE "recurring_contract"
        DROP COLUMN "sds_state_date_old"
        """)
