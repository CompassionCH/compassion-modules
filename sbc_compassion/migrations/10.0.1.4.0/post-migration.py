# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Create a tuple (partner_id, lang_id) for all the res_partners.
    # Adds each row in the relational table
    cr.execute("""
INSERT INTO res_lang_compassion_res_partner_rel
(res_partner_id, res_lang_compassion_id)
(SELECT res_partner.id AS partner_id, res_lang.id AS lang_id FROM res_partner
INNER JOIN res_lang ON res_lang.code = res_partner.lang)
ON CONFLICT
DO NOTHING
    """)
