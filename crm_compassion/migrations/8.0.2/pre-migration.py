# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
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

    # Find all origins related to partners
    cr.execute("""
        SELECT o.id AS oid, a.id AS aid
        FROM recurring_contract_origin o JOIN res_users u
          ON o.partner_id = u.partner_id
        JOIN account_analytic_account a ON a.name LIKE '%' || o.name
        WHERE o.type = 'partner' and o.analytic_id IS NULL
        """)
    res_query = cr.dictfetchall()
    for origin in res_query:
        cr.execute("""
            UPDATE recurring_contract_origin
            SET analytic_id = {aid}
            WHERE id = {oid}
            """.format(**origin))
