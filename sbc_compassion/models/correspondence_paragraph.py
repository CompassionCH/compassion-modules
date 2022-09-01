##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import html
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

BOX_SEPARATOR = "#BOX#"
PAGE_SEPARATOR = "#PAGE#"


class CorrespondenceParagraph(models.Model):
    """ This class defines a page used for in sponsorship correspondence"""

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
