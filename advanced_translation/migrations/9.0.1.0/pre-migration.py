# -*- coding: utf-8 -*-
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

    # Move translate data
    cr.execute("""
UPDATE ir_model_data SET module='child_switzerland'
WHERE module = 'advanced_translation' and (
  name LIKE '%_fr' OR name LIKE '%_de' OR name LIKE '%_it')
    """)
