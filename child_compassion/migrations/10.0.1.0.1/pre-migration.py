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

    # Recompute age of sponsored children
    cr.execute("""
UPDATE compassion_child SET age = extract (
    year from age(birthdate :: timestamp))
WHERE state = 'P';
    """)
