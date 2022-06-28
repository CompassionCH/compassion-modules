from odoo import models, fields


class CorrespondenceParagraph(models.Model):
    _inherit = "correspondence.paragraph"

    comments = fields.Text()

    def clean_paragraphs(self):
        """
        Used to remove empty paragraphs if the translator removes elements.
        """
        pages = self.mapped("page_id")
        for paragraph in self:
            if paragraph.original_text or paragraph.english_text:
                paragraph.translated_text = ""
            else:
                paragraph.unlink()
        pages.filtered(lambda p: not p.paragraph_ids).unlink()
        return True
