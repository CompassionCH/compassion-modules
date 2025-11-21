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
        select id, report_id from mis_report_instance
        where name->>'en_US' IN (
            'Sponsorship report', 'Monthly Acquisitions and Cancellations'
        );""")
    res = cr.fetchall()
    instance_ids = tuple(r[0] for r in res)
    report_ids = tuple(r[1] for r in res)

    if instance_ids:
        cr.execute(
            "DELETE FROM mis_report_instance WHERE id = ANY(%s);",
            (list(instance_ids),),
        )
    if report_ids:
        cr.execute(
            "DELETE FROM mis_report WHERE id = ANY(%s);",
            (list(report_ids),),
        )
