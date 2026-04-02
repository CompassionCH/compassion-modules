import json

from odoo import models


class GMCMessage(models.Model):
    _inherit = "gmc.message"

    def _migrate_correspondence(self):
        for message in self:
            try:
                letter_ids = message._parse_object_ids()
                if not letter_ids:
                    continue
                letters_without_pages = self.env["correspondence"].search(
                    [("id", "in", letter_ids), ("page_ids", "=", False)]
                )
                letters_with_pages = self.env["correspondence"].search(
                    [("id", "in", letter_ids), ("page_ids", "!=", False)]
                )
                letters = letters_without_pages + letters_with_pages
                content = json.loads(message.content)
                final_url = content.get("CloudinaryFinalURL")
                original_url = content.get("CloudinaryOriginalURL")
                if letters and (final_url or original_url):
                    for letter in letters_without_pages:
                        letter._create_missing_pages(len(content.get("Pages", [])))
                    letters.write(
                        {
                            "cloudinary_final_letter_url": final_url,
                            "cloudinary_original_letter_url": original_url or False,
                            "sponsor_letter_scan": False,
                        }
                    )
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
