from odoo import models, fields


class CorrespondenceParagraph(models.Model):
    _inherit = "correspondence.paragraph"

    comments = fields.Text()

    def clean_paragraphs(self):
        """
        Used to remove empty paragraphs if the translator removes elements.
        """
        for paragraph in self:
            if paragraph.original_text or paragraph.english_text:
                paragraph.translated_text = False
            else:
                paragraph.unlink()
        return True
