# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Coninckx David <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return
    # Modify analytic accounts linked to Events to change their event type.

    cr.execute(
        """
        INSERT INTO compassion_translated_value
        (is_tag,value_en, property_name)
        SELECT False, distance_from_closest_city, 'distance_from_closest_city'
        FROM compassion_project
        WHERE distance_from_closest_city IS NOT NULL ;
        """)
