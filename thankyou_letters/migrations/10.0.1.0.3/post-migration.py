# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Monzione Marco
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        UPDATE success_story s SET body_text = body, body = NULL
        WHERE s.type = 'sentence'
    """)
