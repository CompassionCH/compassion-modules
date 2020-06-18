from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return
    openupgrade.load_xml(cr, 'crm_compassion', 'data/demand_planning.xml')
