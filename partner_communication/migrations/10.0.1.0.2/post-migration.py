# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    env.cr.execute("""
        UPDATE res_partner
        SET thankyou_letter='only_email', tax_certificate='only_email',
            letter_delivery_preference='auto_digital_only',
            global_communication_delivery_preference='auto_digital_only',
            photo_delivery_preference='auto_digital_only',
            thankyou_preference='auto_digital_only',
            tax_receipt_preference='auto_digital_only'
        WHERE email_only=true
        """)
