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

    # Change 'casestudy' states to 'biennial'
    cr.execute(
        """
        UPDATE recurring_contract
        SET gmc_state = 'biennial'
        WHERE gmc_state = 'casestudy'
        """)
