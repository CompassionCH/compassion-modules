def migrate(cr, version):
    cr.execute("""
        UPDATE recurring_contract SET color=8 WHERE color=1;
        UPDATE recurring_contract SET color=10 WHERE color=5;
        UPDATE recurring_contract SET color=1 WHERE color=2;
    """)
