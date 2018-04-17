# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
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

    # Put missing medium on SUB sponsorships
    direct_medium_id = env.ref('utm.utm_medium_direct').id
    sponsorships = env['recurring.contract'].search([
        ('parent_id', '!=', False),
        ('medium_id', '=', False)
    ])
    sponsorships.write({'medium_id': direct_medium_id})
