# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import StringIO
from odoo import models, fields
from pyPdf.pdf import PdfFileReader, PdfFileWriter
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas


class CorrespondenceLayoutBox(models.Model):
    """ This class defines a translation box that is inside a layout.
    It is useful to know where to insert translation during composition
    process.
    The coordinates are given in inches in order to use ReportLab for
    the composition.
    """

    _name = 'correspondence.layout.box'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char()
    left = fields.Float()
    top = fields.Float()
    width = fields.Float()
    nb_lines = fields.Integer(
        help='Maximum lines authorized in the box.'
    )
    type = fields.Selection([('text', 'Text'), ('photo', 'Photo')])

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_pdf(self, text, use_design=False):
        """
        Given the text, produces an A4 blank PDF with the text put in the
        position given by the tranlsation box.
        :param text: Text to put inside a translation box
        :param use_design: Set to true to use a design in the background
        :return: Rendered PDF
        :rtype: pypdf.PdfFileReader if use_design is False or PdfFileWriter
        """
        self.ensure_one()
        packet = StringIO.StringIO()
        can = Canvas(packet, bottomup=0)
        text_wrap = self._wrap_text(text, can._fontname, can._fontsize)
        top = self.top*inch
        left = self.left*inch
        for line in text_wrap[:self.nb_lines+1]:
            can.drawString(left, top, line)
            top += can._leading
        can.save()
        # Move to the beginning of the StringIO buffer
        packet.seek(0)
        remaining = ''
        if len(text_wrap) > self.nb_lines:
            remaining = ' '.join(text_wrap[self.nb_lines+1:])
        out_pdf = PdfFileReader(packet)
        if use_design:
            design_pdf_path = self.env['ir.config_parameter'].get_param(
                'sbc_compassion.composition_design')
            if design_pdf_path:
                design_pdf = PdfFileReader(file(design_pdf_path, 'rb'))
                page = design_pdf.getPage(0)
                page.mergePage(out_pdf.getPage(0))
                page.compressContentStreams()
                out_pdf = PdfFileWriter()
                out_pdf.addPage(page)
        return out_pdf, remaining

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
        text_wrap = list()
        for line in text.split('\n'):
            text_width = stringWidth(line, font_name, font_size) / inch
            line_wrap = list()
            if text_width > self.width:
                ratio = self.width / text_width
                line_length = int(len(line) * ratio)
                words = line.split(' ')
                sub_line = ''
                for word in words:
                    if len(sub_line) + len(word) < line_length:
                        sub_line += word + ' '
                    else:
                        line_wrap.append(sub_line)
                        sub_line = word + ' '
                line_wrap.append(sub_line)
            else:
                line_wrap = [line]
            text_wrap.extend(line_wrap)

        return text_wrap
