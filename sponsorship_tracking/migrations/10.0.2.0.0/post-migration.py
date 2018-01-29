# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    cr = env.cr
    # Remove end reason on active sponsorships
    cr.execute("""
        UPDATE recurring_contract
        SET end_reason = NULL
        WHERE STATE NOT IN
        ('terminated', 'cancelled');
    """)
    # Remove waiting_welcome state of non sponsorship contracts
    # or old contracts
    cr.execute("""
            UPDATE recurring_contract
            SET sds_state = 'active'
            WHERE sds_state = 'waiting_welcome'
            AND (type not in ('S', 'SC')
                 OR sds_state_date < current_date - INTERVAL '15 days');
        """)
