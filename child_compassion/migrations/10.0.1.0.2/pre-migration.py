# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Remove duplicated lifecycle events
    cr.execute("""
        DELETE FROM compassion_project_ile duplicate
        USING compassion_project_ile master
        WHERE duplicate.id < master.id
        AND duplicate.name = master.name
    """)
