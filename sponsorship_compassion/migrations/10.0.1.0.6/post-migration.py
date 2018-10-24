# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade

import random


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    old_sponsorships = env['recurring.contract'].search([
        ('type', 'like', 'S'),
        ('state', '=', 'terminated'),
        ('global_id', '=', False),
        ('activation_date', '!=', False)
    ])

    random_global_ids = range(0, 1000000)
    random.shuffle(random_global_ids)

    min_days_duration = 10

    for sponsorship in old_sponsorships.filtered(
            lambda s: s.contract_duration > min_days_duration):
        sponsorship.write({
            'global_id': 'missing-' + str(random_global_ids.pop())
        })
