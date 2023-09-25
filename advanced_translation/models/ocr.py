import logging
import re
import shlex
import string

import pytesseract
from PIL import ImageEnhance, ImageOps

from odoo import models

logger = logging.getLogger(__name__)


class OCR(models.AbstractModel):
    _name = "ocr"
    _description = "Optical character recognition with Tesseract"

    _languages_tesseract = ["eng", "fra", "deu", "ita", "spa"]
    _accents = "çäïüëöâîûêôáíúéóàìùèò"
    _punctuation = " .,!?-()"
    _char_whitelist = shlex.quote(
        string.ascii_letters
        + string.digits
        + _punctuation
        + _accents
        + _accents.upper()
    )
    _config = (
        rf"-c tessedit_char_whitelist={_char_whitelist} -l "
        rf"{'+'.join(_languages_tesseract)} --dpi 300"
    )

    def image_to_string(self, image):
        # use greyscale, cause some letters use color pencils
        image = ImageOps.grayscale(image)

        image = ImageEnhance.Contrast(image).enhance(1.5)

        logger.debug(self._config)
        text = pytesseract.image_to_string(image, config=self._config)
        # remove every invisible character (line breaks, etc..) by spaces
        text = re.sub(r"\s+", " ", text)
        logger.debug(text)
        return text, image
