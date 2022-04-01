

def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        UPDATE account_invoice
        SET auto_cancel_date = NOW()
        WHERE auto_cancel_no_transaction = true
        AND state IN ('draft', 'open')
    """)
