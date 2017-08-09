# -*- encoding: utf-8 -*-
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
        UPDATE res.partner p
        SET number_sponsorships = (SELECT count(*)
                                   FROM recurring.contract c
                                   WHERE c.partner_id = p.id)
    """)
