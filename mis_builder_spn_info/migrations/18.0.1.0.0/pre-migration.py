def migrate(cr, version):
    cr.execute("""
    DELETE FROM ir_ui_view WHERE model = 'res.config.settings'
    AND arch_db LIKE '%mis_%';
    """)
