from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr, """
            UPDATE ir_model_data SET noupdate=False WHERE name='intervention_details_request';
            UPDATE ir_model_data SET noupdate=False WHERE name='update_intervention_details';
            UPDATE ir_model_data SET noupdate=False WHERE name='create_intervention_details';
            UPDATE ir_model_data SET noupdate=False WHERE name='create_intervention_opt_in';
            UPDATE ir_model_data SET noupdate=False WHERE name='intervention_search_action';
            UPDATE ir_model_data SET noupdate=False WHERE name='intervention_create_hold_action';
            UPDATE ir_model_data SET noupdate=False WHERE name='intervention_update_hold_action';
            UPDATE ir_model_data SET noupdate=False WHERE name='intervention_cancel_hold_action';
            UPDATE ir_model_data SET noupdate=False WHERE name='intervention_hold_removal_notification';
            UPDATE ir_model_data SET noupdate=False WHERE name='intervention_reporting_milestone';
            UPDATE ir_model_data SET noupdate=False WHERE name='intervention_amendment_commitment_notification';
            UPDATE ir_model_data SET noupdate=False WHERE name='intervention_create_commitment_action';
            UPDATE ir_model_data SET noupdate=False WHERE name='icp_kit';
            UPDATE ir_model_data SET noupdate=False WHERE name='update_letter';
            UPDATE ir_model_data SET noupdate=False WHERE name='create_letter';
            UPDATE ir_model_data SET noupdate=False WHERE name='upsert_partner';
            UPDATE ir_model_data SET noupdate=False WHERE name='anonymize_partner';
            UPDATE ir_model_data SET noupdate=False WHERE name='create_sponsorship';
            UPDATE ir_model_data SET noupdate=False WHERE name='update_sponsorship';
            UPDATE ir_model_data SET noupdate=False WHERE name='cancel_sponsorship';
        """,
    )

