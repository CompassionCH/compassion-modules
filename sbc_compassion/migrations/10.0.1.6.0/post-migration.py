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
    from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
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
    """
    if not version:
        return

    # Filters correspondences that can safely drop the PDF and regenerate it later
    correspondences = env['correspondence'].search([
        '&',
        '&',
        '&',
        '&',
        '|',
        ('source', '=', 'website'),
        ('source', '=', 'compassion'),
        ('letter_format', '=', 'pdf'),
        ('direction', '=', 'Supporter To Beneficiary'),
        ('template_id', '!=', False),
        ('store_letter_image', '=', True)
    ])

    templates_backgrounds_sizes = retrieve_background_sizes(env)

    correspondences = correspondences.filtered(lambda x: x.id in [27788, 108590])
    migrated = env['correspondence']

    _logger.info(
        "updating {} correspondences"
        .format(len(correspondences))
    )

    for c in correspondences:
        try:
            # Read the PDF in memory
            pdf_data = BytesIO(base64.b64decode(c.letter_image))

            # Retrieve the text. If we fail, we don't want to delete the PDF.
            original_text = extract_text_from_pdf(pdf_data)
            if not original_text or len(original_text) < 50:
                continue

            # Retrieve optional sponsor's images.
            attachments = extract_attachment_from_pdf(pdf_data,
                                                      templates_backgrounds_sizes)

            # Retrieve the text in 'original_text'. It is usually not the original_text
            # But the translated one sent to GMC. We wants to move it to 'english_text'
            english_text = c.original_text
            c.page_ids.unlink()

            # Write the modififications
            attachment_vals = []
            for filename in attachments:
                buffered = BytesIO()
                attachments[filename].save(buffered, format="JPEG")
                attachment_vals.append((0, 0, {
                    'datas_fname': filename,
                    'datas': base64.b64encode(buffered.getvalue()),
                    'name': filename,
                    'res_model': c._name,
                }))

            c.write({
                'letter_image': False,
                'store_letter_image': False,
                'original_attachment_ids': attachment_vals,
                'original_text': original_text,
                'english_text': english_text
            })
            migrated += c
        except Exception as e:
            _logger.error("Failed migration of correspondence with id %d" % c.id)
            _logger.error(str(e))

    _logger.info("successfully migrated {}/{} correspondences".format(
        len(migrated), len(correspondences)))
    return True


def retrieve_background_sizes(env):
    """
    List the sizes of all templates' backgrounds
    """
    templates = env['correspondence.template'].search([])
    sizes = set()
    for template in templates:
        for page in template.page_ids:
            if page.background:
                img = Image.open(BytesIO(base64.b64decode(page.background)))
                sizes.add((img.width, img.height))
    return sizes


def extract_text_from_pdf(pdf_data):
    """
    Extract and concatenate all text boxes from a PDF (BytesIO stream)
    """
    text = ""
    parser = PDFParser(pdf_data)
    document = PDFDocument(parser)
    resmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(resmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(resmgr, device)

    headers = ""
    first_page = True
    for page in PDFPage.create_pages(document):
        interpreter.process_page(page)
        for obj in device.get_result():
            if isinstance(obj, (LTTextBox, LTTextLine)):
                if first_page:
                    if obj.y0 > device.result.height*0.9:
                        headers = obj._objs
                    else:
                        text += obj.get_text().replace('\n', ' ') + '\n'
                else:
                    if obj._objs[0].get_text() != headers[0].get_text():
                        text += obj.get_text().replace('\n', ' ') + '\n'
        first_page = False
    return text


def extract_attachment_from_pdf(pdf_data, size_filter=None):
    """
    Extract images from a PDF (BytesIO stream)

    We don't want to export backgrounds (which are saved in templates) to save disk
    space. We use the images dimensions to detect and filter those.
    """
    images = {}
    encoders = {
        '/DCTDecode': '.jpg',
        '/JPXDecode': '.jp2',
        '/CCITTFaxDecode': '.tiff',
        # '/FlatDecode': '.png'
    }
    if size_filter is None:
        size_filter = []

    pdf = PyPDF2.PdfFileReader(pdf_data)
    x_object = pdf.getPage(0)['/Resources']['/XObject'].getObject()
    
    for obj in x_object:
        if x_object[obj]['/Subtype'] == '/Image':
            size = (x_object[obj]['/Width'], x_object[obj]['/Height'])
            if size in size_filter:
                continue

            data = x_object[obj].getData()
            if '/Filter' in x_object[obj]:
                _filter = x_object[obj]['/Filter']
                if _filter in encoders:
                    img = Image.open(BytesIO(data))
                    filename = obj[1:] + encoders[_filter]
                else:
                    mode = x_object[obj]['/ColorSpace'] == '/DeviceRGB' and "RGB" or "P"
                    img = Image.frombytes(mode, size, data)
                    filename = obj[1:] + '.png'
                images[filename] = img
    return images



