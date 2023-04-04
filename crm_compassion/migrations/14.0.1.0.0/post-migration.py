from openupgradelib import openupgrade


def migrate(cr, version):
    # Reload noupdate data
    openupgrade.load_data(cr, "crm_compassion", "security/crm_compassion_security.xml")
