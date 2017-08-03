# -*- coding: utf-8 -*-
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

    # Put analytic tags
    cr.execute("""
    SELECT analytic_id, type FROM crm_event_compassion
    WHERE analytic_id IS NOT NULL;
    """)
    for row in cr.fetchall():
        aid = row[0]
        type = row[1]
        cr.execute("""
        INSERT INTO account_analytic_account_tag_rel (account_id, tag_id)
        VALUES ({}, (SELECT id FROM account_analytic_tag
                     WHERE name ~* '{}'))
        """.format(aid, type))
