##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade
from odoo.addons.intervention_compassion import load_mappings


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    load_mappings(env.cr, env)
