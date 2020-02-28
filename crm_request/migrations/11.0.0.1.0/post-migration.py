##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Get all existing claim_types
    env.cr.execute("SELECT * FROM crm_claim_type")
    # Create a claim category for each claim type
    for claim_type in env.cr.dictfetchall():
        new_cat = env['crm.claim.category'].create({
            'name': claim_type['name'],
            'template_id': claim_type['template_id'],
            'description': claim_type['description'],
        })
        env.cr.execute("UPDATE crm_claim SET categ_id = %s WHERE claim_type = %s",
                       [new_cat.id, claim_type['id']])
