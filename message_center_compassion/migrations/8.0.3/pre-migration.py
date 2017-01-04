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
DELETE FROM gmc_message_pool where action_id = 9 AND state IN ('new',
    'pending') AND invoice_line_id IS NULL; -- Delete invalid gifts.
UPDATE gmc_message_pool SET date = '2017-02-24' WHERE date < '2017-02-24'
    AND action_id = 9;
ALTER TABLE gmc_message_pool ADD COLUMN old_action character varying;
ALTER TABLE gmc_message_pool ALTER COLUMN action_id DROP NOT NULL;
UPDATE gmc_message_pool m SET old_action = (
    SELECT name from gmc_action where id = m.action_id
), action_id = NULL
WHERE action_id NOT IN (
  SELECT id FROM gmc_action WHERE name IN ('CreateCommKit', 'UpdateCommKit')
);
DELETE FROM gmc_action WHERE name NOT IN ('CreateCommKit', 'UpdateCommKit');
    """)

    # Reconstruct security rules
    cr.execute("""
UPDATE ir_model_data SET module = 'message_center_compassion'
WHERE name = 'module_category_compassion';
    """)

    # Move fields from module onramp_compassion
    cr.execute("""
UPDATE ir_model_data SET module = 'message_center_compassion'
WHERE name IN ('field_gmc_message_pool_content',
               'field_gmc_message_pool_headers');
    """)

    # Move field gmc_state to module sponsorship_switzerland
    cr.execute("""
UPDATE ir_model_data SET module='sponsorship_switzerland'
WHERE name = 'field_recurring_contract_gmc_state'
    """)
