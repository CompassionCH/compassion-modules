# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    """
    move the `original_text` to `english_text`
    then, try to extract texts and images from the PDF. They will be stored in
    `original_attachment_ids` and `original_text`

    To avoid processing all the correspondences at the same time (that would block
    the server for a long time) we split the task in batches and process them in
    queue jobs.

    Jobs have a low priority and their ETA ensure they start after the server startup
    """
    if not version:
        return

    batch_size = 10
    job_options = {
        'priority': 11,  # default = 10
        'max_retries': 2,  # default = 5
        'eta': datetime.today() + relativedelta(minutes=10),
        'channel': 'root.sbc_compassion_migration',
        'description': 'sbc_compassion PDF storage migration (10.0.1.6.0)'
    }

    # Filters correspondences that can drop the PDF and regenerate it later
    correspondences_ids = env['correspondence'].search([
        '|',
        ('source', '=', 'website'),
        ('source', '=', 'compassion'),
        ('letter_format', '=', 'pdf'),
        ('direction', '=', 'Supporter To Beneficiary'),
        ('store_letter_image', '=', True),
        ('template_id', '!=', False),
        ('letter_image', '!=', False)
    ]).ids

    _logger.info("Creating {} Job Queues, migrating {} correspondences".format(
        len(correspondences_ids) // batch_size + 1, len(correspondences_ids)))

    for i in range(0, len(correspondences_ids), batch_size):
        batch = correspondences_ids[i:i+batch_size]
        env['correspondence.migration'].with_delay(**job_options).migrate(
            batch)
