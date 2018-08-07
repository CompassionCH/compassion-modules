# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    env.cr.execute("""
        INSERT INTO partner_communication_omr_config (
            config_id,
            omr_enable_marks,
            omr_should_close_envelope,
            omr_add_attachment_tray_1,
            omr_add_attachment_tray_2
        ) SELECT
            id,
            omr_enable_marks,
            omr_should_close_envelope,
            omr_add_attachment_tray_1,
            omr_add_attachment_tray_2
        FROM partner_communication_config;
    """)
