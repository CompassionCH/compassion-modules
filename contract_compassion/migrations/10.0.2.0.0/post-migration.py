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

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Restore channels
    channel_mapping = {
        'postal': env.ref('contract_compassion.utm_medium_post').id,
        'direct': env.ref('utm.utm_medium_direct').id,
        'email': env.ref('utm.utm_medium_email').id,
        'internet': env.ref('utm.utm_medium_website').id,
        'phone': env.ref('utm.utm_medium_phone').id,
        'payment': env.ref('contract_compassion.utm_medium_payment').id,
    }
    for old_channel, new_channel_id in channel_mapping.iteritems():
        env.cr.execute("""
            UPDATE recurring_contract SET medium_id = %s
            WHERE channel_backup = %s;
        """, [new_channel_id, old_channel])

    # Move sub channel to sub campaign
    sub_campaign_id = env.ref('contract_compassion.utm_campaign_sub').id
    sub_source_id = env.ref('contract_compassion.utm_source_sub').id
    env.cr.execute("""
        UPDATE recurring_contract SET campaign_id = %s, source_id = %s
        WHERE channel_backup = 'sub' """, [sub_campaign_id, sub_source_id])
    env.cr.execute("""
      ALTER TABLE recurring_contract DROP COLUMN channel_backup;
    """)

    # Move SUB origin to SUB source
    sub_origin_id = env['recurring.contract.origin'].search([
        ('name', '=', 'SUB Sponsorship')]).id
    env.cr.execute("""
        UPDATE recurring_contract SET campaign_id = %s, source_id = %s
        WHERE origin_id = %s """, [sub_campaign_id, sub_source_id,
                                   sub_origin_id])

    inactivate_utms = [
        'utm_medium_television',
        'utm_campaign_fall_drive',
        'utm_campaign_email_campaign_services',
        'utm_campaign_email_campaign_products',
        'utm_source_search_engine',
        'utm_source_mailing',
        'utm_source_newsletter',
        'utm_source_facebook',
        'utm_source_twitter',
        'utm_campaign_christmas_special',
    ]
    for utm in inactivate_utms:
        env.ref('utm.' + utm).active = False
