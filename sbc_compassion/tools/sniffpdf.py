##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Girardin <emmanuel.girardin@outlook.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
# All the code here has been inspired from these two web pages:
# http://nedbatchelder.com/blog/200712/extracting_jpgs_from_pdfs.html
# https://www.binpress.com/tutorial/manipulating-pdfs-with-python/167


import os
import logging
from io import StringIO

_logger = logging.getLogger(__name__)

try:
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter, PDFPageAggregator
    from pdfminer.layout import LAParams, LTImage
    from pdfminer.pdfpage import PDFPage
except ImportError:
    _logger.error('Please install pdfminer to use SBC module')


def get_images(pdf_data, dst_folder, dst_name):
    # the following is from that blog:
    # http://nedbatchelder.com/blog/200712/extracting_jpgs_from_pdfs.html
    startmark = b"\xff\xd8"
    startfix = 0
    endmark = b"\xff\xd9"
    endfix = 2
    i = 0

    filenames = []
    njpg = 0
    while True:
        istream = pdf_data.find(b"stream", i)
        if istream < 0:
            break
        istart = pdf_data.find(startmark, istream, istream + 20)
        if istart < 0:
            i = istream + 20
            continue
        iend = pdf_data.find(b"endstream", istart)
        if iend < 0:
            raise Exception("Didn't find end of stream!")
        iend = pdf_data.find(endmark, iend - 20)
        if iend < 0:
            raise Exception("Didn't find end of JPG!")

        istart += startfix
        iend += endfix
        jpg = pdf_data[istart:iend]

        # save image number N at required location
        filname = f"{dst_folder}/{dst_name}{njpg}.jpg"
        with open(filname, "wb") as jpgfile:
            jpgfile.write(jpg)

        filenames.append(filname)
        njpg += 1
        i = iend
    return filenames


def data2pdf(pdf_data, dst_url=None):
    if not dst_url:
        dst_url = os.getcwd() + '/sniffpdf_gettext_tmp.pdf'
    with open(dst_url, 'wb') as tmp:
        tmp.write(pdf_data)
    return dst_url


def get_text(url, pages=None):
    # this one has been adapted from there
    # https://www.binpress.com/tutorial/manipulating-pdfs-with-python/167
    # and has been slightly modified

    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    with open(url, 'rb') as infile:
        # should be a single page, but iterate anyway
        for page in PDFPage.get_pages(infile, pagenums):
            interpreter.process_page(page)
    converter.close()
    text = output.getvalue()
    output.close()
    return text


def get_layout(url, pages=None):
    """
    The layout is an object of pdfminer corresponding to the tree structure of
    a pdf. More information about the layout here:
    http://www.unixuser.org/~euske/python/pdfminer/programming.html
    :param url: path (str) of the pdf file to be analysed
    :param pages: list (int) of pages of which you want the layout.
    Beware
    that
    the first page of the pdf correspond to number 0, even if its id is 1
    :return layouts: List of layouts (One layout per page).
    """
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    # Set parameters for analysis.
    laparams = LAParams()
    manager = PDFResourceManager()
    # Create a PDF page aggregator object.
    device = PDFPageAggregator(manager, laparams=laparams)
    interpreter = PDFPageInterpreter(manager, device)
    layouts = []
    with open(url, 'rb') as infile:
        for page in PDFPage.get_pages(infile, pagenos=pagenums):
            interpreter.process_page(page)
            layouts.append(device.get_result())
    device.close()

    return layouts


def contains_a_single_image(LTObject):
    """
    Return True only if these 2 conditions are True:
        1) The layout tree contains a single leaf
        2) The leaf is an image. (layout object of type LTImage)
    It means that the tree can be made of several nodes, but each
    node has a single child which is either another node or an image. This
    function will recursively walk trough the tree.
    :param LTObject: The current node
    :return:
    """

    if hasattr(LTObject, '_objs'):
        if len(LTObject._objs) != 1:
            return False
        else:
            return contains_a_single_image(LTObject._objs[0])
    else:
        return isinstance(LTObject, LTImage)
