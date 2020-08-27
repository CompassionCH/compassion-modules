# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    for partner_id in env["res.partner"].search([]):
        app_messages = env["mobile.app.messages"].create({
            "partner_id": partner_id.id
        })
        partner_id.app_messages = app_messages
