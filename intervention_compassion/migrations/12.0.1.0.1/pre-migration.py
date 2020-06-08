from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.delete_records_safely_by_xml_id(
        env, ['intervention_compassion.intervention_sla_check_done'])
    openupgrade.rename_xmlids(env.cr, [
        ('intervention_compassion.intervention_sla_check',
         'intervention_compassion.intervention_sla_check_done')
    ])
