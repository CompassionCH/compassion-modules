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

    # Force reloading security groups
    openupgrade.load_xml(env.cr, 'child_compassion', 'security/sponsorship_groups.xml')

    # Add admin groups
    sponsorship_manager_group = env.ref('child_compassion.group_manager')
    env['res.users'].search([
        ('login', 'in', ['ecino', 'dwulliamoz', 'seicher', 'admin',
                         'sherrendorff']),
    ]).write({
        'groups_id': [(4, sponsorship_manager_group.id)]
    })
