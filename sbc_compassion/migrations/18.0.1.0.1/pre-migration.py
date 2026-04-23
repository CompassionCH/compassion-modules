def migrate(cr, version):
    cr.execute("""
    UPDATE ir_act_window
    SET path=NULL
    WHERE path='letters';
""")
