# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Update pictures older pictures that don't have a link
    cr.execute("""
        UPDATE compassion_child_pictures AS pics
        SET image_url = CONCAT(
            'https://erp.compassion.ch/web/image/compassion.child.pictures/',
            id,
            '/fullshot/child.jpg'
        )
        WHERE (pics.image_url <> '') IS NOT TRUE
    """)

