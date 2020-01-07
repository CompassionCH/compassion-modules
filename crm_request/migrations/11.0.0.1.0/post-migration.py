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
    env.cr.execute("""
        SELECT *
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'public'
        AND TABLE_NAME = 'crm_claim_type'; 
    """)

    # Add each one to the claim categories
    for claim_type in env.cr.dictfetchall():
        env['crm.claim.category'].create({
            'id': claim_type['id'],
            'name': claim_type['name'],
            'template_id': claim_type['template_id'],
            'description': claim_type['description'],
        })
