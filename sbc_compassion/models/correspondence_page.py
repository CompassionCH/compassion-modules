##############################################################################
#
#    Copyright (C) 2014-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <eicher31@hotmail.com>
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


class CorrespondencePage(models.Model):
    """ This class defines a page used for in sponsorship correspondence"""

    _inherit = "compassion.mapped.model"
    _name = "correspondence.page"
    _description = "Letter page"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    correspondence_id = fields.Many2one(
        "correspondence", ondelete="cascade", required=True, readonly=False
    )
    original_page_url = fields.Char()
    final_page_url = fields.Char()
    paragraph_ids = fields.One2many("correspondence.paragraph", "page_id", "Paragraphs")
    original_text = fields.Text(default="", readonly=True)
    english_text = fields.Text(default="", readonly=True)
    translated_text = fields.Text(default="", readonly=True)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    _sql_constraints = [
        (
            "original_page_url",
            "unique(original_page_url)",
            _("The pages already exists in database."),
        ),
        (
            "final_page_url",
            "unique(final_page_url)",
            _("The pages already exists in database."),
        ),
    ]

    @api.multi
    def sync_text_from_paragraphs(self):
        _fields = ["original_text", "english_text", "translated_text"]
        for page in self:
            page.write({
                field: BOX_SEPARATOR.join(page.mapped("paragraph_ids").mapped(field))
                for field in _fields
            })
        return True

    @api.model
    def json_to_data(self, json, mapping_name=None):
        odoo_data = super().json_to_data(json, mapping_name)
        odoo_fields = ("original_text", "english_text", "translated_text")
        if isinstance(odoo_data, dict):
            odoo_data = [odoo_data]
        for field in odoo_fields:
            for page_data in odoo_data:
                if field in page_data:
                    page_data[field] = html.unescape(
                        BOX_SEPARATOR.join(page_data[field])
                    )
        return odoo_data
