import pytesseract
import shlex
import string

from odoo import models


class OCR(models.AbstractModel):
    _name = "ocr"
    _description = "Optical character recognition with Tesseract"

    _languages_tesseract = ["eng", "fra", "deu", "ita", "por", "spa", "osd"]
    _chars = shlex.quote(string.printable)
    _config = rf"-c tessedit_char_whitelist={_chars} --psm 6 -l {'+'.join(_languages_tesseract)}"

    def image_to_string(self, image):
        return pytesseract.image_to_string(image, config=self._config)
