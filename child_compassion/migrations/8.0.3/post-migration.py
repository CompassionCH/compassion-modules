# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Child and project codes are one character longer
    cr.execute("""
UPDATE compassion_child SET local_id = left(local_id, 2) || '0' ||
    substring(local_id from 3 for 3) || '0' || right(local_id, 4);
UPDATE compassion_project SET icp_id = left(icp_id, 2) || '0' || right(
    icp_id, 3);
    """)
