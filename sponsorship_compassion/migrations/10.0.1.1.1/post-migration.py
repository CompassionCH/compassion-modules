# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    upsert_action = env.ref('sponsorship_compassion.upsert_partner')
    # Disable autoprocess
    upsert_action.auto_process = False
    # Update all sponsor genders
    sponsors = env['res.partner'].search([
        ('has_sponsorships', '=', True)
    ])
    batch_size = 80
    _logger.info("%s partners to migrate", len(sponsors))
    for i in xrange(0, len(sponsors), batch_size):
        upsert = sponsors[i:i+batch_size].upsert_constituent().with_context(
            async_mode=True)
        _logger.info("Created %s jobs for updating partner gender to GMC",
                     i + batch_size)
        upsert.process_messages()

    # Enable auto_process back
    upsert_action.auto_process = True
    return True
