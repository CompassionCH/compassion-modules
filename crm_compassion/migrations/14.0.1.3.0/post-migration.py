from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE crm_lead
        SET active = FALSE, probability = 0
        WHERE stage_id IN (SELECT id FROM crm_stage WHERE is_lost = TRUE);
        UPDATE crm_lead
        SET stage_id = 211
        WHERE active = FALSE AND probability = 0 AND stage_id NOT IN (SELECT id FROM crm_stage WHERE is_lost = TRUE);
        """
    )