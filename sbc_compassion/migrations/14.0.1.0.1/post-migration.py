from odoo.addons.child_compassion import load_mappings as c_load_mappings
from odoo.addons.message_center_compassion import load_mappings as m_load_mappings
from odoo.addons.sbc_compassion import load_mappings as sbc_load_mappings
from odoo.addons.sponsorship_compassion import load_mappings as s_load_mappings


def migrate(cr, version):
    if version:
        m_load_mappings(cr, cr)
        s_load_mappings(cr, cr)
        c_load_mappings(cr, cr)
        sbc_load_mappings(cr, cr)
