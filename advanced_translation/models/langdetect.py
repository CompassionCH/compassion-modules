import langdetect
import logging
from odoo import models

logger = logging.getLogger(__name__)


class OSD(models.AbstractModel):
    _name = "langdetect"
    _description = "Language detection with langdetect"

    default_threshold = 0.85
    languages_langdetect = ["en", "de", "fr", "it"]

    def detect_language(self, text, threshold=None):
        if threshold is None:
            threshold = self.default_threshold

        languages = langdetect.detect_langs(text)

        logger.debug(languages)

        # ensure that the probabilities are sorted in decreasing order
        languages.sort(key=lambda l: -l.prob)
        # filter languages below the threshold or that are not looked for
        languages = [lang for lang in languages if lang.prob >= threshold and lang.lang in self.languages_langdetect]

        language = self.env["res.lang.compassion"]
        if len(languages) <= 0:
            return language

        language = language.search_iso639(languages[0].lang)
        return language
