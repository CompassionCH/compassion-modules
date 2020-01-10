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

    claim_type_to_category_dict = {}
    # Create a claim category for each claim type
    for claim_type in env.cr.dictfetchall():
        new_cat = env['crm.claim.category'].create({
            'name': claim_type['name'],
            'template_id': claim_type['template_id'],
            'description': claim_type['description'],
        })
        claim_type_to_category_dict[claim_type.id] = new_cat.id

    all_requests = env['crm.claim'].search([
        ('claim_type', '!=', False)
    ])
    # Replace claim type by claim category
    for request in all_requests:
        request.write({
            'claim_category': claim_type_to_category_dict[request.claim_type.id]
        })
