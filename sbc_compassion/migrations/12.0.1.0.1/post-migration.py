from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return
    openupgrade.load_xml(cr, 'sbc_compassion', 'data/gmc_action.xml')
    openupgrade.load_xml(cr, 'child_compassion', 'data/gmc_action.xml')
    openupgrade.load_xml(cr, 'sponsorship_compassion', 'data/gmc_action.xml')
