import logging

import langdetect

from odoo import models

logger = logging.getLogger(__name__)


class OSD(models.AbstractModel):
    _name = "langdetect"
    _description = "Language detection with langdetect"

    default_threshold = 0.95
    languages_langdetect = ["en", "de", "fr", "it", "es"]

    def detect_language(self, text, threshold=None):
        if threshold is None:
            threshold = self.default_threshold

        language = self.env["res.lang.compassion"]

        if not isinstance(text, str) or len(text) < 50:
            return language

        try:
            languages = langdetect.detect_langs(text)
        except Exception:
            return language

        languages = [(lang.lang, lang.prob) for lang in languages]
        logger.debug(languages)

        # ensure that the probabilities are sorted in decreasing order
        languages.sort(key=lambda l: -l[1])
        # filter out languages hat are not looked for
        languages = [lang for lang in languages if lang[0] in self.languages_langdetect]
        sum_p = sum(lang[1] for lang in languages)
        languages = [(lang[0], lang[1] / sum_p) for lang in languages]
        logger.debug(languages)
        languages = [lang for lang in languages if lang[1] >= threshold]

        if len(languages) <= 0:
            return language

        language = language.search_iso639(languages[0][0])
        return language
