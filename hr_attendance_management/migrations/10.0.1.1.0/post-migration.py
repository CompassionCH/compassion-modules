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


def migrate(cr, version):
    if not version:
        return

    # Recompute break duration with new field definition
    cr.execute("""
        UPDATE hr_attendance_break
        SET additional_duration = total_duration - original_duration;
    """)

    # Rename settings
    cr.execute("""
            UPDATE ir_config_parameter
            SET key = replace(key, 'hr_attendance_calendar',
                              'hr_attendance_management')
        """)

    # See https://confluence.compassion.ch/display/CI/Migration+hr-attendance
    # for migration protocol
