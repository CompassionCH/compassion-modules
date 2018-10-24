# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Child and project codes are one character longer
    cr.execute("""
UPDATE compassion_child SET local_id = left(code, 2) || '0' ||
    substring(code from 3 for 3) || '0' || right(code, 4);
UPDATE compassion_project SET fcp_id = left(fcp_id, 2) || '0' || right(
    fcp_id, 3);
    """)
