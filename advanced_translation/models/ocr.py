import pytesseract
import shlex
import string
import logging

from odoo import models

logger = logging.getLogger(__name__)


class OCR(models.AbstractModel):
    _name = "ocr"
    _description = "Optical character recognition with Tesseract"

    _languages_tesseract = ["eng", "fra", "deu", "ita", "por", "spa", "osd"]
    _chars = shlex.quote(string.ascii_letters + string.whitespace + string.digits + ".,!?")
    _config = rf"-c tessedit_char_whitelist={_chars} -l {'+'.join(_languages_tesseract)}"

    def image_to_string(self, image):
        # convert to grey scale
        image = image.convert("L")
        text = pytesseract.image_to_string(image, config=self._config)
        logger.debug(text)
        return text
