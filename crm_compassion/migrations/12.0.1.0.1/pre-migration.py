def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        ALTER TABLE mail_mail
        ADD COLUMN IF NOT EXISTS is_from_employee boolean;
    """)

    cr.execute("""
        ALTER TABLE crm_phonecall
        ADD COLUMN IF NOT EXISTS is_from_employee boolean;
    """)
