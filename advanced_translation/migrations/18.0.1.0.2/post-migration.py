def migrate(cr, version):
    cr.execute("""
        UPDATE ir_advanced_translation
        SET src_fallback = true
        WHERE "group" IN (
            'Caregiver Job',
            'Date format'
        )
        OR "group" IS NULL
""")
