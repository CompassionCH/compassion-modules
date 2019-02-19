# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(env, version):
    if not version:
        return

    env.cr.execute("""
        UPDATE res_partner
        SET thankyou_letter='only_email'
        WHERE email_only=true AND thankyou_letter!='none'
        """)
    env.cr.execute("""
        UPDATE res_partner
        SET tax_certificate='only_email'
        WHERE email_only=true AND tax_certificate!='none'
        """)
    env.cr.execute("""
        UPDATE res_partner
        SET letter_delivery_preference='auto_digital_only'
        WHERE email_only=true AND letter_delivery_preference!='none'
        """)
    env.cr.execute("""
        UPDATE res_partner
        SET global_communication_delivery_preference='auto_digital_only'
        WHERE email_only=true AND
        global_communication_delivery_preference!='none'
        """)
    env.cr.execute("""
        UPDATE res_partner
        SET photo_delivery_preference='auto_digital_only'
        WHERE email_only=true AND photo_delivery_preference!='none'
        """)
    env.cr.execute("""
        UPDATE res_partner
        SET thankyou_preference='auto_digital_only'
        WHERE email_only=true AND thankyou_preference!='none'
        """)
    env.cr.execute("""
        UPDATE res_partner
        SET tax_receipt_preference='auto_digital_only'
        WHERE email_only=true AND tax_receipt_preference!='none'
        """)
