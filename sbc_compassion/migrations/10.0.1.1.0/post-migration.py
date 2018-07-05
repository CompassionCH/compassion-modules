# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Put a default file_name in correspondence to allow retrieving them.
    env.cr.execute("""
        UPDATE correspondence
        SET file_name = kit_identifier || '.pdf'
    """)

    # Migrate correspondence template image
    attachment_obj = env['ir.attachment']
    templates = env['correspondence.template'].search([])
    for template in templates:
        # Restore pattern image from database
        env.cr.execute("""
            SELECT pattern_image FROM correspondence_template
            WHERE id = %s
        """, [template.id])
        pattern_image = env.cr.fetchone()[0]

        # Restore template image from ir.attachment
        template_image = None
        attachment = attachment_obj.search([
            ('res_model', '=', 'correspondence.template'),
            ('res_id', '=', template.id)])
        if attachment:
            template_image = attachment.datas
            attachment.unlink()

        template.write({
            'pattern_image': pattern_image,
            'template_image': template_image
        })
