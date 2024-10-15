def migrate(cr, version):
    # Remove parameters from report paperformat (no longer used)
    cr.execute("DELETE FROM report_paperformat_parameter;")
