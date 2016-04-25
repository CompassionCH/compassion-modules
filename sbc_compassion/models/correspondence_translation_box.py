# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import StringIO
from openerp import models, fields
from pyPdf.pdf import PdfFileReader
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas


class CorrespondenceTranslationBox(models.Model):
    """ This class defines a translation box that is inside a layout.
    It is useful to know where to insert translation during composition
    process.
    The coordinates are given in inches in order to use ReportLab for
    the composition.
    """

    _name = 'correspondence.translation.box'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char()
    text_length = fields.Integer(
        help='Maximum text length authorized in the box. If the text is longer'
             ', it will be cut.')
    left = fields.Float()
    top = fields.Float()
    width = fields.Float()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_pdf(self, text):
        """
        Given the text, produces an A4 blank PDF with the text put in the
        position given by the tranlsation box.
        :param text: Text to put inside a translation box
        :return: Rendered PDF
        :rtype: pypdf.PdfFileReader
        """
        self.ensure_one()
        packet = StringIO.StringIO()
        can = Canvas(packet, bottomup=0)
        text_wrap = self._wrap_text(text, can._fontname, can._fontsize)
        top = self.top*inch
        left = self.left*inch
        for line in text_wrap:
            can.drawString(left, top, line)
            top += can._leading
        can.save()
        # Move to the beginning of the StringIO buffer
        packet.seek(0)
        return PdfFileReader(packet)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _wrap_text(self, text, font_name, font_size):
        """
        Wraps the given text so that it can fit inside the translation box.
        :param text: Text to wrap inside the translation box
        :param font_name: Font used for the render
        :param font_size: Font size used for the render
        :return: List of lines
        :rtype: list(str)
        """
        text_width = stringWidth(text, font_name, font_size) / inch
        text_wrap = list()
        if text_width > self.width:
            ratio = self.width / text_width
            line_length = int(len(text) * ratio)
            words = text.split(' ')
            line = ''
            for word in words:
                if len(line) + len(word) < line_length:
                    line += word + ' '
                else:
                    text_wrap.append(line)
                    line = word + ' '
            text_wrap.append(line)
        else:
            text_wrap = [text]

        return text_wrap
