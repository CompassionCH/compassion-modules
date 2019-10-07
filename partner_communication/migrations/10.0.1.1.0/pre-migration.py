
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

    # Save a backup of need_call boolean field
    if not openupgrade.column_exists(cr, 'partner_communication_job',
                                     'need_call_backup'):
        openupgrade.copy_columns(cr, {
            'partner_communication_config': [
                ('need_call', 'need_call_backup', 'boolean')],
            'partner_communication_job': [
                ('need_call', 'need_call_backup', 'boolean')],
        })
