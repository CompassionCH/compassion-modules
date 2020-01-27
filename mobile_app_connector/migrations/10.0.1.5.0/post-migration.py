# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade
import re

TAG_RE = re.compile(r'<[^>]+>')

@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    ios_category = env['crm.claim.category'].sudo().search(
        [('name', 'ilike', 'iOS')])
    android_category = env['crm.claim.category'].sudo().search(
        [('name', 'ilike', 'Android')])

    # Recover all claims made from the app (== android or ios as source)
    claims = env['crm.claim'].search([
        '|',
        ('categ_id', '=', ios_category.id),
        ('categ_id', '=', android_category.id)
    ])

    # Create a mail for each claim
    for claim in claims:
        # Filter requests on description TODO-> have a better way of filtering instead of a static String ?
        og_requests_claims = claim.message_ids.filtered(
            lambda m: "Original request" in m.description)
        if og_requests_claims:
            body = TAG_RE.sub("", og_requests_claims[0].body)
            if body:
                env['mail.mail'].create({
                    'state': 'sent',
                    'subject': claim.subject,
                    'body_html': body,
                    'author_id': claim.partner_id.id,
                    'email_from': TAG_RE.sub("", claim.email_from),
                    'mail_message_id': env['mail.message'].create({
                        'model': 'res.partner',
                        'res_id': claim.partner_id.id,
                        'body': body,
                        'subject': claim.subject,
                        'author_id': claim.partner_id.id,
                        'subtype_id': env.ref('mail.mt_comment').id,
                        'email_from': TAG_RE.sub("", claim.email_from),
                        'date': claim.date,
                    }).id
                })
