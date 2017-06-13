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


def migrate(cr, version):
    if not version:
        return

    # Move lang_data
    cr.execute("""
UPDATE ir_model_data SET module='child_switzerland'
WHERE name IN ('lang_compassion_german', 'lang_compassion_italian');
    """)

    # Move translate data
    cr.execute("""
UPDATE ir_model_data SET module='child_switzerland'
WHERE module = 'child_compassion' and model = 'ir.advanced.translation'
    """)
