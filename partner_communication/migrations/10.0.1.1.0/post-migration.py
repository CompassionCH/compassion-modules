
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Restore need call as before communication sent by default
    cr.execute("""
        UPDATE partner_communication_config
        SET need_call = 'before_sending'
        WHERE need_call_backup IS TRUE;
    """)
    cr.execute("""
        UPDATE partner_communication_job
        SET need_call = 'before_sending'
        WHERE need_call_backup IS TRUE;
    """)
    openupgrade.drop_columns(cr, [
        ('partner_communication_config', 'need_call_backup'),
        ('partner_communication_job', 'need_call_backup'),
    ])
