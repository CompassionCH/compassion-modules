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
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Rename table gmc_message_pool
    openupgrade.rename_tables(cr, [('gmc_message_pool', 'gmc_message')])
    openupgrade.rename_models(cr, [('gmc.message.pool', 'gmc.message')])
