##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

BOX_SEPARATOR = "#BOX#"
PAGE_SEPARATOR = "#PAGE#"


class CorrespondenceParagraph(models.Model):
    """This class defines a page used for in sponsorship correspondence"""

    _inherit = "compassion.mapped.model"
    _name = "correspondence.paragraph"
    _description = "Letter paragraph"
    _order = "page_id,sequence"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    page_id = fields.Many2one(
        "correspondence.page", ondelete="cascade", required=True, index=True
    )
    sequence = fields.Integer(default=0, index=True)
    original_text = fields.Text(default="")
    english_text = fields.Text(default="")
    translated_text = fields.Text(default="")

    _sql_constraints = [
        (
            "unique_paragraph",
            "unique(page_id,sequence)",
            _("The paragraph already exists."),
        )
    ]

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if not self.env.context.get("from_correspondence_text"):
            res.mapped("page_id").sync_text_from_paragraphs()
        return res

    def write(self, vals):
        super().write(vals)
        if not self.env.context.get("from_correspondence_text"):
            self.mapped("page_id").sync_text_from_paragraphs()
        return True

    def unlink(self):
        pages = self.mapped("page_id")
        res = super().unlink()
        if not self.env.context.get("from_correspondence_text"):
            pages.sync_text_from_paragraphs()
        return res

    def fetch_style(self, field_name):
        """
        Get the overlay style for the given field name, used on the Qweb-Report.
        """
        self.ensure_one()
        return self.get_text_box(field_name).css_style

    def check_overflow(self, field_name):
        """
        Check if the text overflows the text box.
        :param field_name: The field name to check for overflow.
        :return: Tuple with (text_that_fits, text_that_overflows)
        """
        self.ensure_one()
        text_box = self.get_text_box(field_name)
        text = self[field_name]
        max_chars = text_box.max_chars
        line_length = text_box.line_size

        if not max_chars or not line_length or not text:
            return text, ""

        text_that_fits, text_that_overflows = self._split_text(
            text, max_chars, line_length
        )
        return self._finalize_text(text_that_fits, text_that_overflows)

    def _split_text(self, text, max_chars, line_length):
        text_that_fits = []
        text_that_overflows = []
        current_line_length = 0
        total_chars = 0
        lbr_replace = "$" * line_length

        for word in text.replace("\n", " " + lbr_replace + " ").split():
            is_lbr = word == lbr_replace
            word_length = len(word) if not is_lbr else line_length - current_line_length
            current_line_length += word_length + 1
            if current_line_length >= line_length:
                current_line_length = 0
            total_chars += word_length + 1
            if total_chars <= max_chars:
                text_that_fits.append(word if not is_lbr else "\n")
            else:
                text_that_overflows.append(word if not is_lbr else "\n")

        return text_that_fits, text_that_overflows

    def _finalize_text(self, text_that_fits, text_that_overflows):
        if text_that_overflows and text_that_fits:
            last_word = text_that_fits.pop()
            text_that_overflows.insert(0, last_word)
            text_that_overflows.insert(0, "...")
            text_that_fits.append("...")
        return " ".join(text_that_fits), " ".join(text_that_overflows)

    def get_text_box(self, field_name):
        """
        Finds the related correspondence.text.box in the template for the given text.
        :param field_name: The field name to search for in the text boxes.
        :return: The related correspondence.text.box
        """
        self.ensure_one()
        page_template = self.page_id.template_id
        text_type = "Original" if field_name == "original_text" else "Translation"
        return page_template.text_box_ids.filtered(lambda x: x.text_type == text_type)[
            self.sequence : self.sequence + 1
        ]
