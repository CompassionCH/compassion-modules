def migrate(cr, version):
    cr.execute("""delete from queue_job_function where name not like '%edi%';""")
