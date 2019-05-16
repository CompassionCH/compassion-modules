# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Find child pictures attachments and map them to child pictures
    pic_objname = 'compassion.child.pictures'
    pictures = env['ir.attachment'].search([
        ('res_model', '=', pic_objname),
        '|', ('name', 'ilike', 'headshot'), ('name', 'ilike', 'fullshot')
    ]).with_context(bin_size=False)
    to_migrate = pictures.filtered('datas')
    total = len(to_migrate)
    for count, picture in enumerate(to_migrate):
        _logger.info('Migrating picture %s/%s', count+1, total)
        pic_record = env[pic_objname].browse(picture.res_id)
        # Spread the jobs with 3 seconds interval
        pic_record.with_delay(eta=3*count)\
            .migrate_unlink_old_attachments(picture)
