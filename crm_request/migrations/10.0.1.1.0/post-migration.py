# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Link all mail_messages of crm_requests to their associated partners
    cr.execute("""
        UPDATE mail_message m
        SET author_id = c.partner_id
        FROM crm_claim c
        WHERE  m.res_id = c.id
        AND c.partner_id IS NOT NULL
        AND m.model = 'crm.claim'
        AND m.author_id IS NULL
    """)
