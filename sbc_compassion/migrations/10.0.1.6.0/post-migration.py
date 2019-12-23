# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import base64
from io import BytesIO
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

try:
    import PyPDF2
    from PIL import Image

    from pdfminer.converter import PDFPageAggregator
    from pdfminer.layout import LAParams, LTTextBox, LTTextLine
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdfparser import PDFParser

except ImportError:
    _logger.error("Python libraries 'PyPDF2', 'pdfminer' and 'Pillow' are required for"
                  " the correspondences migration in order to extract images from PDFs")


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    """
    move the `original_text` to `english_text`
    then, try to extract texts and images from the PDF. They will be stored in
    `original_attachment_ids` and `original_text`

    To avoid processing all the correspondences at the same time (that would block
    the server for a long time) we split the task in batches and process them in
    queue jobs
    """
    if not version:
        return

    batch_size = 4

    # Filters correspondences that can drop the PDF and regenerate it later
    correspondences = env['correspondence'].search([
        '&', '&', '&', '&', '|',
        ('source', '=', 'website'),
        ('source', '=', 'compassion'),
        ('letter_format', '=', 'pdf'),
        ('direction', '=', 'Supporter To Beneficiary'),
        ('store_letter_image', '=', True)
        ('template_id', '!=', False)
    ])
    correspondences_ids = correspondences.filtered('letter_image').ids

    _logger.info("Creating {} Job Queues, migrating {} correspondences".format(
        len(correspondences_ids) // batch_size, len(correspondences_ids)))

    for i in range(0, len(correspondences_ids), batch_size):
        batch = correspondences_ids[i:i+batch_size]
        env['correspondence.migration'].with_delay().migrate(batch)
