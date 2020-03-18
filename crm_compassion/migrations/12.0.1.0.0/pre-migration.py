def migrate(cr, version):
    if not version:
        return

    # Replace ids of better_zip by ids of city_zip
    cr.execute("""
        ALTER TABLE crm_event_compassion
        DROP CONSTRAINT crm_event_compassion_zip_id_fkey;
        UPDATE crm_event_compassion e
        SET zip_id = (
            SELECT id FROM res_city_zip
            WHERE openupgrade_legacy_12_0_better_zip_id = e.zip_id)
    """)
