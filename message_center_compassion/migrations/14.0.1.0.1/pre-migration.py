

def migrate(cr, version):
        cr.execute("""
            UPDATE compassion_field_to_json
            SET allow_relational_creation = true
            WHERE relational_raise_if_not_found = true;
        """)
