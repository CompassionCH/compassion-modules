from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return
    openupgrade.load_xml(cr, 'intervention_compassion', 'data/gmc_action.xml')
