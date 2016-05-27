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

    # Delete old actions and old processed messages (no history!)
    cr.execute("""
DELETE FROM gmc_message_pool where state = 'success';
ALTER TABLE gmc_message_pool ADD COLUMN old_action character varying;
ALTER TABLE gmc_message_pool ALTER COLUMN action_id DROP NOT NULL;
UPDATE gmc_message_pool m SET old_action = (
    SELECT name from gmc_action where id = m.action_id
), action_id = NULL;
DELETE FROM gmc_action;
    """)

    # Reconstruct security rules
    cr.execute("""
UPDATE ir_model_data SET module = 'message_center_compassion'
WHERE name = 'module_category_compassion';
    """)
