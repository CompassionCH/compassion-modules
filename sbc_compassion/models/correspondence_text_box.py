##############################################################################
#
#    Copyright (C) 2019-2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Théo Nikles <theo.nikles@gmail.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from functools import lru_cache

from PIL import ImageFont

from odoo import fields, models
from odoo.tools.misc import file_path

# wkhtmltopdf renders the px line heights about 25% taller than what the
# height of the boxes were designed for.
WKHTMLTOPDF_LINE_HEIGHT_SCALE = 0.8

# Text layout of the correspondence report (A4 at 96 DPI, see the report CSS),
# used to measure how much text fits in a box.
PAGE_WIDTH_PX = 793.7
PAGE_HEIGHT_PX = 1122.5
FONT_SIZE_PX = 16
PARAGRAPH_MARGIN_PX = 18.9
FONT_FILE = "web/static/fonts/lato/Lato-Reg-webfont.ttf"
# Emojis and symbols are missing from Lato and rendered wider with a fallback font.
FALLBACK_GLYPH_WIDTH_EM = 1.25
CUT_MARK = "..."


class _WordChunk(str):
    """
    Part of a word that was too long for a text box. It continues the previous
    chunk, so it is joined to it without a space.
    """


def _join_words(words):
    text = ""
    for word in words:
        if text and not isinstance(word, _WordChunk):
            text += " "
        text += word
    return text


@lru_cache(maxsize=1)
def _get_font():
    return ImageFont.truetype(file_path(FONT_FILE), 1000)


@lru_cache(maxsize=4096)
def _text_width(text):
    font = _get_font()
    width = font.getlength(text)
    for char in text:
        if ord(char) > 0x2000 and not font.getmask(char).getbbox():
            width += FALLBACK_GLYPH_WIDTH_EM * 1000 - font.getlength(char)
    return width * FONT_SIZE_PX / 1000


class CorrespondenceTextBox(models.Model):
    _name = "correspondence.text.box"
    _description = "Correspondence Text Box"

    name = fields.Char()
    x_min = fields.Float(
        "Left position (%)",
        help="Left position of the object in percents (of the page)",
        required=True,
    )
    y_min = fields.Float(
        "Top position (%)",
        help="Top position of the object in percents (of the page)",
        required=True,
    )
    width = fields.Float(
        "Width (%)",
        help="Width of the object in percents (of the page size)",
        required=True,
    )
    height = fields.Float(
        "Height (%)",
        help="Height of the object in percents (of the page size)",
        required=True,
    )
    text_line_height = fields.Float(help="Line height in pixels", required=True)
    line_size = fields.Integer(
        help="Not used anymore: the text is measured to fit the size of the box."
    )
    max_chars = fields.Integer(
        help="Not used anymore: the text is measured to fit the size of the box."
    )

    text_type = fields.Selection(
        [
            ("Original", "Original"),
            ("Translation", "Translation"),
        ]
    )
    css_style = fields.Char(compute="_compute_css_style")

    def _compute_css_style(self):
        """
        Get the overlay style for the given box, used on the Qweb-Report.
        """
        for text_box in self:
            line_height = text_box.text_line_height * WKHTMLTOPDF_LINE_HEIGHT_SCALE
            text_box.css_style = f"""
                position: absolute;
                top: {text_box.y_min}%;
                left: {text_box.x_min}%;
                width: {text_box.width}%;
                height: {text_box.height}%;
                line-height: {line_height}px;
            """

    def split_text(self, text):
        """
        Lay the text out like the report does and cut it where the box is full.
        :return: Tuple with (text_that_fits, text_that_overflows)
        """
        self.ensure_one()
        max_width = self.width / 100 * PAGE_WIDTH_PX
        max_height = self.height / 100 * PAGE_HEIGHT_PX
        line_height = self.text_line_height * WKHTMLTOPDF_LINE_HEIGHT_SCALE
        # Each line of the text is a paragraph in the report.
        paragraphs = text.split("\n")
        height = 0.0
        for index, paragraph in enumerate(paragraphs):
            lines = self._wrap_lines(paragraph.split(), max_width)
            if lines:
                nb_lines = int((max_height - height) // line_height)
                height += len(lines) * line_height
            else:
                # An empty paragraph keeps the height of one character.
                nb_lines = 0
                height += FONT_SIZE_PX
            if height > max_height:
                return self._cut_text(paragraphs, index, lines, nb_lines, max_width)
            height += PARAGRAPH_MARGIN_PX
        return text, ""

    def _wrap_lines(self, words, max_width):
        lines = []
        line = []
        line_width = 0.0
        space_width = _text_width(" ")
        for word in self._split_long_words(words, max_width):
            word_width = _text_width(word)
            space = space_width if line and not isinstance(word, _WordChunk) else 0
            if line and line_width + space + word_width > max_width:
                lines.append(line)
                line = [word]
                line_width = word_width
            else:
                line.append(word)
                line_width += space + word_width
        if line:
            lines.append(line)
        return lines

    def _split_long_words(self, words, max_width):
        """
        A word wider than the box (long URL, text without spaces) is wrapped by
        the report: we cut it in chunks that are glued back together when the
        text is joined.
        """
        for word in words:
            if _text_width(word) <= max_width:
                yield word
                continue
            chunk = ""
            chunk_class = str
            for char in word:
                if chunk and _text_width(chunk + char) > max_width:
                    yield chunk_class(chunk)
                    chunk = ""
                    chunk_class = _WordChunk
                chunk += char
            yield chunk_class(chunk)

    def _cut_text(self, paragraphs, index, lines, nb_lines, max_width):
        fit_lines = lines[:nb_lines]
        overflow_words = [word for line in lines[nb_lines:] for word in line]
        if fit_lines and overflow_words:
            # Mark the cut with "..." on both pages.
            last_line = fit_lines[-1]
            while (
                len(last_line) > 1
                and _text_width(_join_words(last_line + [CUT_MARK])) > max_width
            ):
                overflow_words.insert(0, last_line.pop())
            last_line.append(CUT_MARK)
            # It starts the next page: no previous chunk to be glued to.
            overflow_words[0] = str(overflow_words[0])
            overflow_words.insert(0, CUT_MARK)
        fit_paragraphs = paragraphs[:index]
        if fit_lines:
            fit_paragraphs.append(
                _join_words([word for line in fit_lines for word in line])
            )
        text_that_fits = "\n".join(fit_paragraphs).rstrip()
        overflow_paragraphs = paragraphs[index + 1 :]
        if overflow_words:
            overflow_paragraphs.insert(0, _join_words(overflow_words))
        text_that_overflows = "\n".join(overflow_paragraphs).strip()
        if not text_that_fits:
            # Nothing fits in the box: keep the text here, moving it to the next
            # page would only repeat the same overflow.
            return "\n".join(paragraphs), ""
        return text_that_fits, text_that_overflows
