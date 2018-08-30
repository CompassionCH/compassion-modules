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

    # Update CRON function
    cr.execute(
        """
        UPDATE ir_cron
        SET function = 'hold_children_for_sms_cron'
        WHERE function = 'hold_children_for_sms'
        """
    )
