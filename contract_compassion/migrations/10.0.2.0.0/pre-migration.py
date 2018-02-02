# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Save channel
    env.cr.execute("""
        ALTER TABLE recurring_contract
        ADD COLUMN channel_backup VARCHAR;
        UPDATE recurring_contract SET channel_backup = channel;
    """)

    # Delete mediums not defined in utm module
    env.cr.execute("""
        DELETE from utm_medium
        WHERE id NOT IN
        (SELECT res_id FROM ir_model_data
         WHERE module = 'utm' AND name like 'utm_medium%')
    """)
