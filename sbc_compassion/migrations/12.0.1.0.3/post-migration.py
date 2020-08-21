def migrate(cr, installed_version):
    if not installed_version:
        return

    # Compute date of last_letter for Write&Pray sponsorships
    cr.execute("""
        update recurring_contract c
        set last_sponsor_letter = (
            select max(scanned_date) from correspondence
            where sponsorship_id = c.id and direction = 'Supporter To Beneficiary')
        where state = 'active' and type = 'SC'
    """)
