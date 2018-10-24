# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields
from openupgradelib import openupgrade

import random
import dateutil.parser


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    end_date_limit = dateutil.parser.parse("2016-12-13").date()

    old_sponsorships = env['recurring.contract'].search([
        ('end_date', '<=', fields.Date.to_string(end_date_limit)),
        ('state', '=', 'terminated'),
        ('global_id', '=', False),
        ('activation_date', '!=', False)
    ])

    random_global_ids = range(0, 1000000)
    random.shuffle(random_global_ids)

    min_transmition_delay = 5

    for sponsorship in old_sponsorships.filtered(
            lambda s: s.contract_duration > min_transmition_delay):
        sponsorship.write({
            'global_id': 'missing-' + str(random_global_ids.pop())
        })
