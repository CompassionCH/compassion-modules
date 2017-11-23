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
from dateutil.relativedelta import relativedelta

from odoo import fields
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    list_sponsorships = env['recurring.contract'].search([('parent_id', '!=', False)])

    for sponsorship in list_sponsorships:
        sponsorship.parent_id.sub_sponsorship_id = sponsorship.id
