# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
logger = logging.getLogger()


def migrate(cr, version):
    """ Add partner analytic accounts to origins. """
    if not version:
        return

    # Delete analytic views
    cr.execute("""
    DELETE FROM account_analytic_account WHERE openupgrade_legacy_9_0_type = 'view';
    DELETE FROM account_analytic_account WHERE name in (
        'Presentation', 'Concert', 'Tour');
    UPDATE account_analytic_account SET code = event_type
    WHERE event_type != '';
    UPDATE account_analytic_account SET code = NULL WHERE event_type = '';
    """)
