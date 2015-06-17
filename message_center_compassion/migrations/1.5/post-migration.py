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

    # Remove project_states
    cr.execute(
        """
        UPDATE recurring_contract
        SET gmc_state = NULL
        WHERE gmc_state IN ('suspension', 'suspension-extension',
                            'reactivation')
        """)
