# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Monzione Marco
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    titles = env['res.partner.title'].search([])
    o = {
        'Mister': 0,
        'Madam': 1,
    }

    def set_res_title(t):
        t.order_index = o.get(t.name, 100)

    map(set_res_title, titles)
