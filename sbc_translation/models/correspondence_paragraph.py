from odoo import fields, models


class CorrespondenceParagraph(models.Model):
    _inherit = "correspondence.paragraph"

    comments = fields.Text()

    def clear_paragraphs(self):
        """
        Used to remove empty paragraphs if the translator removes elements.
        """
        for paragraph in self:
            if paragraph.original_text or paragraph.english_text:
                paragraph.write({"translated_text": "", "comments": False})
            else:
                paragraph.unlink()
        return True
