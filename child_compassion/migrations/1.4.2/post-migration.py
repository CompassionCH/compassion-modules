# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Attach last pictures to last case study of children
    cr.execute(
        """
        SELECT cs.id as cs_id, p.id as p_id
        FROM compassion_child_property cs JOIN compassion_child_pictures p
        ON cs.child_id = p.child_id
        WHERE cs.id IN (
            SELECT max(id)
            FROM compassion_child_property
            GROUP BY child_id)
        AND p.id IN (
            SELECT max(id)
            FROM compassion_child_pictures
            GROUP BY child_id)
        ORDER BY cs.child_id
        """)
    to_link = cr.fetchall()
    for data in to_link:
        cr.execute(
            'UPDATE compassion_child_property '
            'SET pictures_id = {0} '
            'WHERE id = {1}; '
            'UPDATE compassion_child_pictures '
            'SET case_study_id = {1} '
            'WHERE id = {0}'.format(data[1], data[0]))
