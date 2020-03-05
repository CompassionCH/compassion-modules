##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Remove bad space in xml_ids of household duties
    cr.execute("""
        UPDATE ir_model_data
        SET name = REGEXP_REPLACE(name, '(household_duty)(.)(_.*)', '\1\3')
        WHERE name like 'household_duty%';
    """)

    # Delete workflows
    openupgrade.delete_model_workflow(cr, 'compassion.child', True)

    # Remove foreign key of old settings tables
    openupgrade.remove_tables_fks(cr, [
        'staff_notification_settings',
        'mobile_app_settings',
        'demand_planning_settings',
        'gifth_threshold_settings',
        'sbc_settings',
        'sds_follower_settings',
        'availability_management_settings',
    ])
    # Drop relation tables of old settings tables
    cr.execute("""
        DROP TABLE res_partner_staff_notification_settings_rel;
        DROP TABLE staff_disaster_notification_ids;
        DROP TABLE staff_gift_notification_ids;
        DROP TABLE invalid_mail_staff_notify_rel;
        DROP TABLE staff_sms_notification_settings;
    """)
