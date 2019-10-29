##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nathan Fluckiger  <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade
from ... import load_mappings


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Put back the end reasons
    end_reason_mapping = {
        '1': env.ref('sponsorship_compassion.end_reason_depart'),
        '2': env.ref('sponsorship_compassion.end_reason_mistake'),
        '3': env.ref('sponsorship_compassion.end_reason_death'),
        '4': env.ref('sponsorship_compassion.end_reason_moved'),
        '5': env.ref('sponsorship_compassion.end_reason_not_satisfied'),
        '6': env.ref('sponsorship_compassion.end_reason_dont_pay'),
        '8': env.ref('sponsorship_compassion.end_reason_personal'),
        '9': env.ref('sponsorship_compassion.end_reason_never_paid'),
        '10': env.ref('sponsorship_compassion.end_reason_subreject'),
        '11': env.ref('sponsorship_compassion.end_reason_sponsor_exchange'),
        '12': env.ref('sponsorship_compassion.end_reason_financial'),
        '13': env.ref('sponsorship_compassion.end_reason_child_exchange'),
        '25': env.ref('sponsorship_compassion.end_reason_not_given'),
    }
    env.cr.execute("""
        SELECT id, end_reason
        FROM recurring_contract
        WHERE end_reason IS NOT NULL
    """)
    for row in env.cr.fetchall():
        env.cr.execute("""
            UPDATE recurring_contract
            SET end_reason_id = %s
            WHERE id = %s
        """, [end_reason_mapping[row[1]].id, row[0]])
    env.cr.execute("""
        ALTER TABLE recurring_contract DROP COLUMN end_reason;
    """)

    load_mappings(env.cr, env)
