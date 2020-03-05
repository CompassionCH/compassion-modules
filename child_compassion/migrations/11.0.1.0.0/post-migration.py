##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nathan Flückiger <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade

from odoo.addons.child_compassion import load_mappings


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    load_mappings(env.cr, env)

    # Add sponsorship group to everyone
    sponsorship_group = env.ref('child_compassion.group_sponsorship')
    env['res.users'].search([
        ('internal', '=', True),
        ('email', 'ilike', 'compassion.ch')
    ]).write({
        'groups_id': [(4, sponsorship_group.id)]
    })
    # Add admin groups
    sponsorship_manager_group = env.ref('child_compassion.group_manager')
    gmc_manager_group = env.ref('message_center_compassion.group_gmc_manager')
    env['res.users'].search([
        ('login', 'in', ['ecino', 'dwulliamoz', 'seicher', 'admin']),
    ]).write({
        'groups_id': [(4, sponsorship_manager_group.id), (4, gmc_manager_group.id)]
    })
