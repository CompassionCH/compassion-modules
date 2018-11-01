# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
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

    # Define the translation date of letters
    translated_letters = env['correspondence'].search([
        ('translator_id', '!=', False)
    ])
    for letter in translated_letters:
        if letter.direction == 'Beneficiary To Supporter':
            translate_date = letter.status_date
        else:
            # For supporter letters we must find when it was translated
            tracking_change = env['mail.tracking.value'].search([
                ('mail_message_id', 'in', letter.message_ids.ids),
                ('field', '=', 'state'),
                ('old_value_char', '=', 'To Translate'),
                ('new_value_char', '=', 'Scanned in')
            ], order='id desc', limit=1)
            translate_date = tracking_change.create_date or \
                letter.scanned_date + ' 12:00:00'
        env.cr.execute("""
            UPDATE correspondence
            SET translate_date = %s
            WHERE id = %s
        """, [translate_date, letter.id])
