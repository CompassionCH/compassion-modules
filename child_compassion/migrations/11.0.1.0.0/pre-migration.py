##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Remove bad space in xml_ids of household duties
    cr.execute("""
        UPDATE ir_model_data
        SET name = REGEXP_REPLACE(name, '(household_duty)(.)(_.*)', '\1\3')
        WHERE name like 'household_duty%';
    """)
