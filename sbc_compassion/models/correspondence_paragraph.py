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

from odoo import api, fields, models

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
            "The paragraph already exists.",
        )
    ]

    @api.model_create_multi
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
        if not text_box or not text:
            return text, ""
        try:
            return text_box.split_text(text)
        except Exception:
            # Never block the creation of a letter: keep the text uncut instead.
            _logger.exception("Could not measure the text of paragraph %s", self.id)
            return text, ""

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
