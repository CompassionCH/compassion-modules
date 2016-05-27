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


def migrate(cr, version):
    if not version:
        return

    # Update children that are in invalid states for R4
    cr.execute("""
UPDATE compassion_child SET state = 'F' WHERE state = 'X';
UPDATE compassion_child SET state = 'N' WHERE state = 'R';
    """)
