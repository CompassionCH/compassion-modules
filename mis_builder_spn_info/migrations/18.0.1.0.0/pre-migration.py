def migrate(cr, version):
    cr.execute("""
  WITH RECURSIVE to_delete AS (
      SELECT id
      FROM ir_ui_view
      WHERE model = 'res.config.settings'
        AND arch_db->>'en_US' LIKE '%mis_%'
      UNION ALL
      SELECT v.id
      FROM ir_ui_view v
      JOIN to_delete td ON v.inherit_id = td.id
    )
    DELETE FROM ir_ui_view
    WHERE id IN (SELECT id FROM to_delete);
    """)
    cr.execute("""
        select report_id from mis_report_instance
        where name->>'en_US' = 'Sponsorship report';""")
    mis_report = cr.fetchone()
    cr.execute("""
        delete from mis_report_instance where name->>'en_US' = 'Sponsorship report';
    """)
    cr.execute(
        """
            delete from mis_report where id = %s;""",
        (mis_report and mis_report[0],),
    )
