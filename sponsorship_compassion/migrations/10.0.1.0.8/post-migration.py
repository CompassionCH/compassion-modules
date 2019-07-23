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

    correspondence = env['recurring.contract'].search([
        ('type', '=', 'SC'),
    ])
    # Put all contract lines amount to 0
    env.cr.execute("""
        UPDATE recurring_contract_line
        SET amount=0, quantity=0, subtotal=0
        WHERE contract_id = ANY (%s);

        UPDATE recurring_contract
        SET total_amount = 0
        WHERE id = ANY (%s);
    """, [correspondence.ids] * 2)
