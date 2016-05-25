# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Update children that are in invalid states for R4
    cr.execute("""
UPDATE compassion_child SET state = 'F' WHERE state = 'F';
UPDATE compassion_child SET state = 'N' WHERE state = 'R';
    """)

    # Add a migration column
    cr.execute("""
ALTER TABLE compassion_child ADD COLUMN to_migrate_r4 boolean;
UPDATE compassion_child set to_migrate_r4 = true WHERE state IN ('N','D','I');
    """)

    # Move Security Rules from child_compassion to message_center_compassion
    # TODO See how to do when message_center is migrated
#     cr.execute("""
# UPDATE ir_model_data
# SET module='message_center_compassion'
# WHERE module='child_compassion' AND
#     name = 'module_category_compassion';
#     """)
