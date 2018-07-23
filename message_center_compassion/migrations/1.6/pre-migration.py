# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def remove_message_duplicates(cr):
    """ Remove message duplicates. """
    cr.execute(
        """
        delete from gmc_message_pool gmc
        where exists (
            select 'x' from gmc_message_pool g1
            where g1.invoice_line_id = gmc.invoice_line_id
            and g1.action_id = gmc.action_id
            and g1.id < gmc.id
        )
        """
    )


def migrate(cr, version):
    if not version:
        return

    remove_message_duplicates(cr)
