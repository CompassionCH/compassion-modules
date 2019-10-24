# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import os
from base64 import b64encode

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Restore B2S correspondence layouts
    cr = env.cr
    cr.execute("""
        UPDATE correspondence c
        SET template_id = (
            SELECT id FROM correspondence_template t
            WHERE t.layout like CONCAT('%', c.b2s_layout, '%')
            AND t.name like 'B2S - L%'
        )
        WHERE c.b2s_layout IS NOT NULL;
    """)

    # Restore template lang checkboxes
    cr.execute("""
    INSERT into correspondence_lang_checkbox_correspondence_template_rel
    SELECT template_id, id
    FROM correspondence_lang_checkbox
    WHERE template_id is not null;
    """)

    # Restore template images and layout config
    l1_1 = env.ref('sbc_compassion.s2b_l1_textbox_original').id
    l1_2 = env.ref('sbc_compassion.s2b_l1_textbox_original2').id
    l3_1_design = env.ref('sbc_compassion.s2b_l3_design').id
    l3_2_text = env.ref('sbc_compassion.s2b_l3_textbox_original').id
    header_box = env.ref('sbc_compassion.s2b_header_box').id
    dir_path = os.path.dirname(os.path.realpath(__file__))
    template_images = [
        f for f in os.listdir(dir_path) if f.endswith('.jpeg')
    ]
    for fname in template_images:
        with open(os.path.join(dir_path, fname), 'r') as template_image:
            data = b64encode(template_image.read())
            template = env['correspondence.template'].search([
                ('name', 'like', fname.replace('.jpeg', ''))
            ])
            p1_text_box_ids = [(4, l1_1)] if template.layout == 'CH-A-1S11-1'\
                else False
            p1_design = [(4, l3_1_design)] if template.layout == 'CH-A-3S01-1'\
                else False
            p2_text_box_ids = [(4, l1_2 if template.layout == 'CH-A-1S11-1'
                               else l3_2_text)]
            template.write({
                'page_ids': [
                    (0, 0, {
                        'background': data,
                        'text_box_ids': p1_text_box_ids,
                        'image_box_ids': p1_design,
                        'header_box_id': header_box
                    }),
                    (0, 0, {
                        'text_box_ids': p2_text_box_ids,
                        'page_index': 2
                    })
                ],
            })
