

def migrate(cr, installed_version):
    if not installed_version:
        return
    cr.execute("""
        UPDATE partner_log_other_interaction
        SET date = create_date;
    """)
