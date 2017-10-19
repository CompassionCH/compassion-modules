# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Move old actions of onramp_compassion
    cr.execute("""
UPDATE ir_model_data SET module = 'sbc_compassion', name = 'update_letter'
WHERE name = 'update_commkit';
UPDATE ir_model_data SET module = 'sbc_compassion', name = 'create_letter'
WHERE name = 'create_commkit';
    """)

    # Move fields from module onramp_compassion
    cr.execute("""
UPDATE ir_model_data SET module = 'sbc_compassion'
WHERE module = 'onramp_compassion' AND model = 'ir.model.fields';
    """)
