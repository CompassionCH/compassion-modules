# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Store the B2S layout of the correspondences
    cr.execute("""
    ALTER TABLE correspondence ADD COLUMN b2s_layout varchar;
    UPDATE correspondence c
    SET b2s_layout = (
        SELECT code from correspondence_b2s_layout l WHERE l.id=c.b2s_layout_id
    ),
        b2s_layout_id = NULL;
    """)

    # Drop all references to table b2s_layout which is removed
    cr.execute("""
    DELETE FROM ir_model_data WHERE model = 'correspondence.b2s.layout';
    """)
