# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=False)
def migrate(cr, version):
    if not version:
        return

    # Move translate data
    cr.execute("""
UPDATE ir_model_data SET module='child_switzerland'
WHERE module = 'child_compassion' and model = 'ir.advanced.translation'
    """)

    # Move data
    openupgrade.rename_xmlids(cr, [
        ('crm_compassion.create_demand_planning', 'child_compassion.create_demand_planning'),
        ('child_compassion.lang_compassion_german', 'child_switzerland.lang_compassion_german'),
        ('child_compassion.lang_compassion_italian', 'child_switzerland.lang_compassion_italian'),
    ])
