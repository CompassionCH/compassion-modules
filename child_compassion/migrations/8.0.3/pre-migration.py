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
UPDATE compassion_child SET state = 'F' WHERE state = 'X';
UPDATE compassion_child SET state = 'N' WHERE state = 'R';
    """)

    # Move languages from sbc_compassion module
    cr.execute("""
    UPDATE ir_model_data SET module = 'child_compassion'
    WHERE module = 'sbc_compassion' AND name LIKE 'lang_compassion%';
        """)

    # Save transfer country for restoring it in contracts
    cr.execute("""
ALTER TABLE compassion_child ADD COLUMN transfer_country_backup INTEGER;
UPDATE compassion_child SET transfer_country_backup = transfer_country_id;
    """)
