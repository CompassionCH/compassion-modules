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
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    for partner in env['res.partner'].search(
            ['partner.title.gender', '!=', False]):
        if partner.title.name not in ['Madam', 'Mister', 'Misters', 'Ladies']:
            # send update to GMC
            partner.upsert_constituent()
