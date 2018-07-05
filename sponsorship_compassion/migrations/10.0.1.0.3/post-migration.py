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

    # Set preferred_name for all partners
    missing = env['res.partner'].search([
        ('preferred_name', '=', False)])
    for partner in missing:
        partner.preferred_name = \
            partner.firstname or partner.lastname or partner.name
