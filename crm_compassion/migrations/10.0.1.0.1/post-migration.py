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

import logging
logger = logging.getLogger()

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Correct ambassadors of sponsorships made from events
    events = env['crm.event.compassion'].search([
        ('origin_id', '!=', False),
        ('user_id', '!=', False)
    ])
    for event in events:
        event.origin_id.partner_id = event.user_id.partner_id
