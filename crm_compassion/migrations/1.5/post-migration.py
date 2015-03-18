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
    # cr.execute(
        # """
        # UPDATE payment_line
        # SET transit_move_line_id = banking_addons_61_debit_move_line_id
        # """)
    # cr.execute(
        # """
        # ALTER TABLE "payment_line"
        # DROP COLUMN "banking_addons_61_debit_move_line_id"
        # """)
