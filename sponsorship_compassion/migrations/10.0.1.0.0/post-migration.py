# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Fluckiger Nathan
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    cr = env.cr
    cr.execute("""
        UPDATE res_partner p
        SET number_sponsorships = (SELECT count(c.*)
                                   FROM recurring_contract c
                                   JOIN res_partner m ON c.partner_id = m.id
                                   JOIN res_partner s
                                   ON c.correspondant_id = m.id
                                   WHERE (((c.partner_id = p.id
                                         OR c.correspondant_id = p.id)
                                         AND c.child_id IS NOT NULL
                                         AND c.state = 'active'
                                         )OR ((m.church_id = p.id or
                                              s.church_id = p.id)
                                         AND c.child_id IS NOT NULL
                                         AND c.state = 'active' )))
    """)
