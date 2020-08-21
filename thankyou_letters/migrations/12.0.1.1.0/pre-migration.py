def migrate(cr, version):
    # Remove old views
    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE MODEL = 'account.invoice'
        AND arch_db LIKE '%avoid_mobile_donation_notification%';
    """)
